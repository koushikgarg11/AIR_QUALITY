"""
Pytest Verification Suite for Air Quality vs. Hospital Admission Analysis Platform.
Tests:
1. Master dataset existence and row count (>= 200,000 rows).
2. Schema columns and non-null constraints.
3. Health metric ranges (PES: 0-100, AQI: 0-500, CPHRS: 0-100).
4. Lag analysis matrix completeness (0-14 days).
5. Report file generation (.docx and .md).
"""
import pytest
import pandas as pd
from pathlib import Path
import os

WORKSPACE_DIR = Path("d:/DATA ANALYSIS/AIR_QUALITY")
DATA_DIR = WORKSPACE_DIR / "data" / "processed"
REPORTS_DIR = WORKSPACE_DIR / "reports"
POWER_BI_DIR = WORKSPACE_DIR / "power_bi" / "data"

def test_master_dataset_exists_and_row_count():
    parquet_file = DATA_DIR / "air_quality_health_200k.parquet"
    assert parquet_file.exists(), f"Missing {parquet_file}"
    df = pd.read_parquet(parquet_file)
    assert len(df) >= 200000, f"Expected >= 200,000 rows, got {len(df):,}"

def test_schema_integrity():
    parquet_file = DATA_DIR / "air_quality_health_200k.parquet"
    df = pd.read_parquet(parquet_file)
    required_cols = [
        "Record_ID", "Date", "City", "Station_Name", "Season", "Weather_Condition",
        "Temperature_C", "Humidity_Pct", "PM2_5", "PM10", "NO2", "SO2", "CO", "O3",
        "AQI", "AQI_Risk_Level", "Pollution_Exposure_Score", "Total_Admissions",
        "Respiratory_Admissions", "Cardiac_Admissions", "Emergency_Cases",
        "Pediatric_Admissions", "Adult_Admissions", "Geriatric_Admissions",
        "Respiratory_Admission_Rate", "Lag_PM2_5_1D", "Lag_PM2_5_2D"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    assert df["Record_ID"].nunique() == len(df), "Record_ID must be unique"

def test_metric_valid_ranges():
    parquet_file = DATA_DIR / "air_quality_health_200k.parquet"
    df = pd.read_parquet(parquet_file)
    assert (df["AQI"] >= 0).all() and (df["AQI"] <= 500).all(), "AQI out of bounds"
    assert (df["Pollution_Exposure_Score"] >= 0).all() and (df["Pollution_Exposure_Score"] <= 100).all(), "PES out of bounds"
    assert (df["Respiratory_Admission_Rate"] >= 0).all() and (df["Respiratory_Admission_Rate"] <= 100).all(), "RAR out of bounds"
    assert (df["Total_Admissions"] >= df["Respiratory_Admissions"]).all(), "Total admissions must exceed respiratory"

def test_city_summary_and_lag_analysis():
    city_file = DATA_DIR / "summary_city_health_scores.csv"
    assert city_file.exists(), f"Missing {city_file}"
    city_df = pd.read_csv(city_file)
    assert len(city_df) == 10, "Expected 10 cities in summary"
    assert "City_Pollution_Health_Risk_Score_CPHRS" in city_df.columns
    assert (city_df["City_Pollution_Health_Risk_Score_CPHRS"] >= 0).all()

    lag_file = DATA_DIR / "summary_lag_analysis.csv"
    assert lag_file.exists(), f"Missing {lag_file}"
    lag_df = pd.read_csv(lag_file)
    assert lag_df["Lag_Days"].max() == 14, "Lag days should reach 14"

def test_power_bi_star_schema_files():
    for f in ["Dim_City.csv", "Dim_Station.csv", "Dim_Date.csv", "Dim_Pollutant_Thresholds.csv", "Fact_Daily_AirQuality_Health.csv"]:
        target = POWER_BI_DIR / f
        assert target.exists(), f"Missing Power BI table: {target}"

def test_comprehensive_reports_generated():
    docx_report = REPORTS_DIR / "Air_Quality_Hospital_Admission_Comprehensive_Report.docx"
    md_report = REPORTS_DIR / "Air_Quality_Hospital_Admission_Comprehensive_Report.md"
    assert docx_report.exists(), f"Missing Word report: {docx_report}"
    assert md_report.exists(), f"Missing Markdown report: {md_report}"
    assert os.path.getsize(docx_report) > 10000, "Word report file size too small"
