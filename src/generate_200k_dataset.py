"""
High-Performance Generator for 200,000+ Air Quality vs. Hospital Admission Records.
Generates 4 full years (2021-2024) across 10 major metropolitan cities and 56 stations,
with 3 daily shift/ward observation records per station-day = 262,980 rows.
Includes seasonal weather dynamics, multi-lag exposure responses, age vulnerability,
and exports to CSV, Parquet, SQLite, and Power BI Star Schema.
"""
import sys
import os
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Import config from scratch or local
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CITIES_CONFIG, POLLUTANT_THRESHOLDS, AQI_BANDS, START_DATE, END_DATE

# Setup target paths
WORKSPACE_DIR = Path("d:/DATA ANALYSIS/AIR_QUALITY")
DATA_DIR = WORKSPACE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
POWER_BI_DATA_DIR = WORKSPACE_DIR / "power_bi" / "data"
REPORTS_DIR = WORKSPACE_DIR / "reports"

for d in [RAW_DIR, PROCESSED_DIR, POWER_BI_DATA_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"

def compute_cpcb_aqi(pm25, pm10, no2, so2, co, o3):
    """Computes Indian CPCB sub-index based AQI."""
    def sub_index(val, breakpoints):
        for (low_c, high_c, low_i, high_i) in breakpoints:
            if low_c <= val <= high_c:
                return low_i + (val - low_c) * (high_i - low_i) / (high_c - low_c)
        if val > breakpoints[-1][1]:
            return breakpoints[-1][3] + (val - breakpoints[-1][1]) * 0.5
        return 0

    pm25_bp = [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200), (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)]
    pm10_bp = [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200), (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)]
    no2_bp = [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200), (180, 280, 201, 300), (280, 400, 301, 400), (400, 600, 401, 500)]
    so2_bp = [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200), (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2500, 401, 500)]
    co_bp = [(0, 1, 0, 50), (1, 2, 51, 100), (2, 10, 101, 200), (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)]
    o3_bp = [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200), (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)]

    i_pm25 = np.vectorize(lambda x: sub_index(x, pm25_bp))(pm25)
    i_pm10 = np.vectorize(lambda x: sub_index(x, pm10_bp))(pm10)
    i_no2 = np.vectorize(lambda x: sub_index(x, no2_bp))(no2)
    i_so2 = np.vectorize(lambda x: sub_index(x, so2_bp))(so2)
    i_co = np.vectorize(lambda x: sub_index(x, co_bp))(co)
    i_o3 = np.vectorize(lambda x: sub_index(x, o3_bp))(o3)

    aqi = np.maximum.reduce([i_pm25, i_pm10, i_no2, i_so2, i_co, i_o3])
    return np.round(np.clip(aqi, 15, 500), 1)

def get_aqi_bucket(aqi_val):
    if aqi_val <= 50:
        return "Good"
    elif aqi_val <= 100:
        return "Satisfactory"
    elif aqi_val <= 200:
        return "Moderate"
    elif aqi_val <= 300:
        return "Poor"
    elif aqi_val <= 400:
        return "Very Poor"
    else:
        return "Severe"

def generate_master_200k_dataset():
    print("=" * 70)
    print("Starting Generation of 200,000+ Air Quality vs. Health Records...")
    print("=" * 70)

    np.random.seed(42)
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
    n_days = len(date_range)  # 1461 days (4 full years)
    
    shifts = [
        {"name": "Morning (06:00-14:00)", "code": "MORN", "weight": 0.38, "traffic_mult": 1.25},
        {"name": "Evening (14:00-22:00)", "code": "EVE", "weight": 0.42, "traffic_mult": 1.35},
        {"name": "Night (22:00-06:00)", "code": "NGT", "weight": 0.20, "traffic_mult": 0.70},
    ]
    
    records = []
    station_meta = []
    city_meta = []
    
    record_id_counter = 1
    
    total_stations = sum(len(cfg["stations"]) for cfg in CITIES_CONFIG.values())
    print(f"Scope: {len(CITIES_CONFIG)} Cities | {total_stations} Stations | {n_days} Days | 3 Shifts/Wards")
    expected_rows = total_stations * n_days * len(shifts)
    print(f"Target Total Rows: {expected_rows:,} records")

    for city_idx, (city_name, city_cfg) in enumerate(CITIES_CONFIG.items(), 1):
        state = city_cfg["state"]
        tier = city_cfg["tier"]
        pop_base = city_cfg["population_base"]
        base_pm25 = city_cfg["base_pm25"]
        base_pm10 = city_cfg["base_pm10"]
        base_no2 = city_cfg["base_no2"]
        base_so2 = city_cfg["base_so2"]
        base_co = city_cfg["base_co"]
        base_o3 = city_cfg["base_o3"]
        base_admissions = city_cfg["base_admissions"]
        winter_factor = city_cfg["winter_spike_factor"]
        lat = city_cfg["latitude"]
        lon = city_cfg["longitude"]

        city_meta.append({
            "CityKey": city_idx,
            "City": city_name,
            "State": state,
            "Tier": tier,
            "Population": pop_base,
            "Latitude": lat,
            "Longitude": lon,
            "StationsCount": len(city_cfg["stations"])
        })

        # Generate base multi-year daily meteorological and atmospheric curves
        day_of_year = date_range.dayofyear.values
        # Seasonal cycle: Peak in winter (Dec/Jan), minimum in monsoon (Jul/Aug)
        # Cosine peak at day 1 (Jan 1) and day 365
        seasonal_pollution_wave = 1.0 + (winter_factor - 1.0) * 0.5 * (1 + np.cos(2 * np.pi * (day_of_year - 15) / 365.25))
        
        # Stubble burning / festival spike in Post-Monsoon (Oct 20 - Nov 20, days 293 to 325)
        post_monsoon_spike = np.where(
            (day_of_year >= 293) & (day_of_year <= 325),
            1.4 if city_name in ["Delhi NCR", "Lucknow", "Patna"] else 1.15,
            1.0
        )
        
        # Monsoon rain washout (Jun 15 - Sep 15, days 166 to 258)
        monsoon_washout = np.where(
            (day_of_year >= 166) & (day_of_year <= 258),
            0.50 if city_name in ["Mumbai", "Kolkata", "Bengaluru", "Chennai"] else 0.65,
            1.0
        )

        # Baseline weather variables
        temp_cycle = 26.0 - 9.0 * np.cos(2 * np.pi * (day_of_year - 140) / 365.25) # Hot in May-June, Cool in Jan
        humidity_cycle = 55.0 + 30.0 * np.sin(2 * np.pi * (day_of_year - 120) / 365.25) # High in monsoon

        for stn_idx, station_name in enumerate(city_cfg["stations"], 1):
            station_key = f"{city_idx:02d}_{stn_idx:02d}"
            stn_lat = lat + (np.random.rand() - 0.5) * 0.15
            stn_lon = lon + (np.random.rand() - 0.5) * 0.15
            
            station_meta.append({
                "StationKey": station_key,
                "CityKey": city_idx,
                "City": city_name,
                "StationName": station_name,
                "Latitude": round(stn_lat, 4),
                "Longitude": round(stn_lon, 4)
            })

            # Station-specific industrial / traffic multiplier
            stn_mult = 1.0 + (stn_idx - len(city_cfg["stations"])/2) * 0.08

            # Autoregressive AR(1) pollution generation across days
            noise_pm25 = np.zeros(n_days)
            noise_pm10 = np.zeros(n_days)
            for t in range(1, n_days):
                noise_pm25[t] = 0.65 * noise_pm25[t-1] + np.random.normal(0, 12)
                noise_pm10[t] = 0.60 * noise_pm10[t-1] + np.random.normal(0, 22)

            daily_pm25 = (base_pm25 * seasonal_pollution_wave * post_monsoon_spike * monsoon_washout * stn_mult + noise_pm25)
            daily_pm25 = np.clip(daily_pm25, 8.0, 480.0)

            daily_pm10 = (base_pm10 * seasonal_pollution_wave * post_monsoon_spike * monsoon_washout * stn_mult + noise_pm10)
            daily_pm10 = np.clip(daily_pm10, 18.0, 680.0)

            daily_no2 = np.clip(base_no2 * seasonal_pollution_wave * 0.85 + np.random.normal(0, 8, n_days), 6.0, 280.0)
            daily_so2 = np.clip(base_so2 + np.random.normal(0, 3, n_days), 3.0, 120.0)
            daily_co = np.clip(base_co * (seasonal_pollution_wave ** 0.5) + np.random.normal(0, 0.2, n_days), 0.2, 14.0)
            daily_o3 = np.clip(base_o3 + 12.0 * np.sin(2 * np.pi * day_of_year / 365.25) + np.random.normal(0, 6, n_days), 5.0, 190.0)

            daily_temp = temp_cycle + np.random.normal(0, 2.5, n_days)
            daily_humidity = np.clip(humidity_cycle + np.random.normal(0, 8, n_days), 15.0, 98.0)
            daily_wind = np.clip(8.0 + 4.0 * np.sin(2 * np.pi * day_of_year / 180) + np.random.normal(0, 3, n_days), 1.0, 35.0)

            daily_aqi = compute_cpcb_aqi(daily_pm25, daily_pm10, daily_no2, daily_so2, daily_co, daily_o3)

            # Health Admissions Modeling with Real Epidemiological Lag:
            # Same-day and 2-4 day lagged PM2.5 heavily drives respiratory illness
            # Cardiac admissions respond to same-day & 1-day lag and cold temperature
            lag_pm25_1 = np.roll(daily_pm25, 1); lag_pm25_1[0] = daily_pm25[0]
            lag_pm25_2 = np.roll(daily_pm25, 2); lag_pm25_2[:2] = daily_pm25[0]
            lag_pm25_3 = np.roll(daily_pm25, 3); lag_pm25_3[:3] = daily_pm25[0]
            lag_pm25_7 = np.roll(daily_pm25, 7); lag_pm25_7[:7] = daily_pm25[0]

            # Weighted distributed lag exposure index
            cum_lag_pm25 = 0.20 * daily_pm25 + 0.35 * lag_pm25_2 + 0.30 * lag_pm25_3 + 0.15 * lag_pm25_7
            
            # Non-linear excess relative risk (surge above 120 ug/m3)
            nonlinear_surge = np.where(cum_lag_pm25 > 120, 1.35 * (cum_lag_pm25 / 120) ** 0.45, 1.0)
            cold_stress_cardiac = np.where(daily_temp < 15, 1.25, 1.0)

            stn_daily_base_adm = (base_admissions / len(city_cfg["stations"]))
            
            # Respiratory admissions (sensitive to lag 2-3 PM2.5 and PM10)
            daily_resp_adm = (
                stn_daily_base_adm * 0.32 * (1.0 + 0.0035 * cum_lag_pm25) * nonlinear_surge + np.random.normal(0, 4, n_days)
            )
            daily_resp_adm = np.clip(np.round(daily_resp_adm), 5, 250).astype(int)

            # Cardiac admissions (sensitive to same-day PM2.5 and cold stress)
            daily_cardiac_adm = (
                stn_daily_base_adm * 0.26 * (1.0 + 0.0022 * daily_pm25) * cold_stress_cardiac + np.random.normal(0, 3, n_days)
            )
            daily_cardiac_adm = np.clip(np.round(daily_cardiac_adm), 4, 180).astype(int)

            # Emergency & Other acute cases
            daily_emerg_adm = (
                stn_daily_base_adm * 0.22 * (1.0 + 0.0028 * daily_pm25) + np.random.normal(0, 3, n_days)
            )
            daily_emerg_adm = np.clip(np.round(daily_emerg_adm), 3, 150).astype(int)

            daily_other_adm = np.clip(
                np.round(stn_daily_base_adm * 0.20 + np.random.normal(0, 3, n_days)), 3, 120
            ).astype(int)

            daily_total_adm = daily_resp_adm + daily_cardiac_adm + daily_emerg_adm + daily_other_adm

            # Age Stratification
            # Children: 32% (high respiratory vulnerability), Elderly: 38% (high cardiac + respiratory), Adults: 30%
            daily_pediatric = np.round(daily_resp_adm * 0.52 + daily_other_adm * 0.22).astype(int)
            daily_geriatric = np.round(daily_cardiac_adm * 0.58 + daily_resp_adm * 0.35 + daily_emerg_adm * 0.30).astype(int)
            daily_adult = np.maximum(daily_total_adm - (daily_pediatric + daily_geriatric), 2).astype(int)

            # Weather Condition classification
            weather_conditions = []
            for d_idx in range(n_days):
                rh = daily_humidity[d_idx]
                t = daily_temp[d_idx]
                aq = daily_aqi[d_idx]
                if rh > 80 and date_range[d_idx].month in [6, 7, 8, 9]:
                    weather_conditions.append("Rainy" if np.random.rand() > 0.3 else "Thunderstorm")
                elif aq > 300 and t < 18:
                    weather_conditions.append("Smog / Fog")
                elif aq > 200:
                    weather_conditions.append("Hazy")
                elif rh > 65:
                    weather_conditions.append("Overcast")
                else:
                    weather_conditions.append("Clear Sky")

            # Expand into 3 shift/ward intake observation records per station-day
            for d_idx, date_val in enumerate(date_range):
                date_str = date_val.strftime("%Y-%m-%d")
                season_str = get_season(date_val.month)
                aqi_val = daily_aqi[d_idx]
                aqi_bucket = get_aqi_bucket(aqi_val)

                # Pollution Exposure Score (PES: 0-100)
                pes = (
                    0.35 * min(100, (daily_pm25[d_idx] / 60.0) * 50) +
                    0.25 * min(100, (daily_pm10[d_idx] / 100.0) * 50) +
                    0.15 * min(100, (daily_no2[d_idx] / 80.0) * 50) +
                    0.10 * min(100, (daily_so2[d_idx] / 80.0) * 50) +
                    0.05 * min(100, (daily_co[d_idx] / 2.0) * 50) +
                    0.10 * min(100, (daily_o3[d_idx] / 100.0) * 50)
                )
                pes = round(min(100.0, max(5.0, pes)), 1)

                for shift in shifts:
                    shift_w = shift["weight"]
                    shift_mult = shift["traffic_mult"]
                    
                    s_pm25 = round(daily_pm25[d_idx] * shift_mult * np.random.uniform(0.92, 1.08), 1)
                    s_pm10 = round(daily_pm10[d_idx] * shift_mult * np.random.uniform(0.92, 1.08), 1)
                    s_no2 = round(daily_no2[d_idx] * shift_mult * np.random.uniform(0.92, 1.08), 1)
                    s_so2 = round(daily_so2[d_idx] * np.random.uniform(0.95, 1.05), 1)
                    s_co = round(daily_co[d_idx] * shift_mult * np.random.uniform(0.92, 1.08), 2)
                    s_o3 = round(daily_o3[d_idx] * (1.3 if "Afternoon" in shift["name"] else 0.8), 1)

                    s_tot_adm = max(1, int(round(daily_total_adm[d_idx] * shift_w + np.random.uniform(-1, 1))))
                    s_resp_adm = max(0, min(s_tot_adm, int(round(daily_resp_adm[d_idx] * shift_w + np.random.uniform(-0.5, 0.5)))))
                    s_card_adm = max(0, min(s_tot_adm - s_resp_adm, int(round(daily_cardiac_adm[d_idx] * shift_w))))
                    s_emerg = max(0, int(round(daily_emerg_adm[d_idx] * shift_w)))
                    
                    s_ped = max(0, int(round(daily_pediatric[d_idx] * shift_w)))
                    s_ger = max(0, int(round(daily_geriatric[d_idx] * shift_w)))
                    s_adult = max(0, s_tot_adm - (s_ped + s_ger))

                    rar = round((s_resp_adm / s_tot_adm) * 100.0, 2) if s_tot_adm > 0 else 0.0

                    records.append({
                        "Record_ID": f"REC_{record_id_counter:07d}",
                        "Date": date_str,
                        "Year": date_val.year,
                        "Month": date_val.month,
                        "Month_Name": date_val.strftime("%b"),
                        "Day_of_Week": date_val.strftime("%a"),
                        "Is_Weekend": 1 if date_val.weekday() >= 5 else 0,
                        "Shift_Time": shift["name"],
                        "Shift_Code": shift["code"],
                        "City": city_name,
                        "State": state,
                        "Tier": tier,
                        "Station_Name": station_name,
                        "Station_Key": station_key,
                        "Latitude": round(stn_lat, 4),
                        "Longitude": round(stn_lon, 4),
                        "Season": season_str,
                        "Weather_Condition": weather_conditions[d_idx],
                        "Temperature_C": round(daily_temp[d_idx] + np.random.uniform(-1.5, 1.5), 1),
                        "Humidity_Pct": round(daily_humidity[d_idx] + np.random.uniform(-3, 3), 1),
                        "Wind_Speed_kmh": round(daily_wind[d_idx] + np.random.uniform(-1, 1), 1),
                        "PM2_5": s_pm25,
                        "PM10": s_pm10,
                        "NO2": s_no2,
                        "SO2": s_so2,
                        "CO": s_co,
                        "O3": s_o3,
                        "AQI": aqi_val,
                        "AQI_Risk_Level": aqi_bucket,
                        "Pollution_Exposure_Score": pes,
                        "Total_Admissions": s_tot_adm,
                        "Respiratory_Admissions": s_resp_adm,
                        "Cardiac_Admissions": s_card_adm,
                        "Emergency_Cases": s_emerg,
                        "Pediatric_Admissions": s_ped,
                        "Adult_Admissions": s_adult,
                        "Geriatric_Admissions": s_ger,
                        "Respiratory_Admission_Rate": rar,
                        "Lag_PM2_5_1D": round(lag_pm25_1[d_idx], 1),
                        "Lag_PM2_5_2D": round(lag_pm25_2[d_idx], 1),
                        "Lag_PM2_5_3D": round(lag_pm25_3[d_idx], 1),
                        "Lag_PM2_5_7D": round(lag_pm25_7[d_idx], 1),
                    })
                    record_id_counter += 1

        print(f"Generated {city_name} records successfully ({record_id_counter-1:,} cumulative rows).")

    df = pd.DataFrame(records)
    print("\nDataset Generation Complete!")
    print(f"Total Rows: {len(df):,} records")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Date Coverage: {df['Date'].min()} to {df['Date'].max()} ({n_days} unique calendar days)")
    print(f"Cities: {df['City'].nunique()} | Stations: {df['Station_Name'].nunique()}")

    # Save to Parquet (High performance) and CSV
    master_parquet_path = PROCESSED_DIR / "air_quality_health_200k.parquet"
    master_csv_path = PROCESSED_DIR / "air_quality_health_200k.csv"
    
    print(f"Writing Parquet to {master_parquet_path}...")
    df.to_parquet(master_parquet_path, index=False, compression="snappy")
    
    print(f"Writing CSV to {master_csv_path}...")
    df.to_csv(master_csv_path, index=False)

    # Save to SQLite Database with Indexes for Instant Queries
    db_path = PROCESSED_DIR / "air_quality_health.db"
    print(f"Populating SQLite Database: {db_path}...")
    conn = sqlite3.connect(db_path)
    df.to_sql("air_quality_health_fact", conn, if_exists="replace", index=False)
    
    # Create indexes for ultra-fast performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON air_quality_health_fact (City);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON air_quality_health_fact (Date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_season ON air_quality_health_fact (Season);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aqi_bucket ON air_quality_health_fact (AQI_Risk_Level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_station ON air_quality_health_fact (Station_Name);")
    conn.commit()
    conn.close()

    # Save Power BI Star Schema Dimensional Tables
    print("Exporting Power BI Dimensional Star Schema tables...")
    dim_city_df = pd.DataFrame(city_meta)
    dim_city_df.to_csv(POWER_BI_DATA_DIR / "Dim_City.csv", index=False)

    dim_station_df = pd.DataFrame(station_meta)
    dim_station_df.to_csv(POWER_BI_DATA_DIR / "Dim_Station.csv", index=False)

    # Dim Date
    dim_date_df = df[["Date", "Year", "Month", "Month_Name", "Day_of_Week", "Is_Weekend", "Season"]].drop_duplicates().sort_values("Date")
    dim_date_df["Quarter"] = pd.to_datetime(dim_date_df["Date"]).dt.quarter
    dim_date_df.to_csv(POWER_BI_DATA_DIR / "Dim_Date.csv", index=False)

    # Thresholds Table
    threshold_records = []
    for pol, vals in POLLUTANT_THRESHOLDS.items():
        threshold_records.append({
            "Pollutant": pol,
            "Unit": vals["unit"],
            "Good_Limit": vals["good"],
            "Satisfactory_Limit": vals["satisfactory"],
            "Moderate_Limit": vals["moderate"],
            "Poor_Limit": vals["poor"],
            "Very_Poor_Limit": vals["very_poor"],
            "Severe_Limit": vals["severe"],
            "Weight": vals["weight"]
        })
    pd.DataFrame(threshold_records).to_csv(POWER_BI_DATA_DIR / "Dim_Pollutant_Thresholds.csv", index=False)

    # Export main Power BI Fact table
    df.to_csv(POWER_BI_DATA_DIR / "Fact_Daily_AirQuality_Health.csv", index=False)

    print("All Datasets Successfully Generated & Exported!")
    return df

if __name__ == "__main__":
    generate_master_200k_dataset()
