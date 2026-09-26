"""
Configuration module for Air Quality vs. Hospital Admission Analysis Platform.
Defines cities, monitoring stations, pollutant standards, scoring weights, and directory paths.
Timeframe: 2022-01-01 to 2025-12-31 (4 full calendar years).
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
POWER_BI_DATA_DIR = BASE_DIR / "power_bi" / "data"
REPORTS_DIR = BASE_DIR / "reports"
SRC_DIR = BASE_DIR / "src"

# Master Cities & Stations Configuration (10 Major Metropolitan Airsheds)
CITIES_CONFIG = {
    "Delhi NCR": {
        "state": "Delhi",
        "tier": "Tier-1 Mega Metro",
        "population_base": 33000000,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "stations": ["Anand Vihar", "Punjabi Bagh", "Dwarka Sector 8", "R K Puram", "IHBAS Dilshad Garden", "Jahangirpuri", "Okhla Phase 2", "Bawana"],
        "base_pm25": 98.0,
        "base_pm10": 195.0,
        "base_no2": 48.0,
        "base_so2": 18.0,
        "base_co": 1.4,
        "base_o3": 38.0,
        "base_admissions": 1250,
        "winter_spike_factor": 2.45,
    },
    "Mumbai": {
        "state": "Maharashtra",
        "tier": "Tier-1 Mega Metro",
        "population_base": 21000000,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "stations": ["Bandra Kurla Complex", "Colaba", "Andheri East", "Kurla West", "Worli", "Borivali East", "Chembur", "Navi Mumbai"],
        "base_pm25": 58.0,
        "base_pm10": 115.0,
        "base_no2": 36.0,
        "base_so2": 14.0,
        "base_co": 1.1,
        "base_o3": 32.0,
        "base_admissions": 950,
        "winter_spike_factor": 1.45,
    },
    "Kolkata": {
        "state": "West Bengal",
        "tier": "Tier-1 Metro",
        "population_base": 15000000,
        "latitude": 22.5726,
        "longitude": 88.3639,
        "stations": ["Victoria Memorial", "Rabindra Bharati", "Ballygunge", "Jadavpur", "Fort William", "Salt Lake Sector 5"],
        "base_pm25": 72.0,
        "base_pm10": 140.0,
        "base_no2": 42.0,
        "base_so2": 16.0,
        "base_co": 1.25,
        "base_o3": 35.0,
        "base_admissions": 720,
        "winter_spike_factor": 1.95,
    },
    "Bengaluru": {
        "state": "Karnataka",
        "tier": "Tier-1 Metro",
        "population_base": 13500000,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "stations": ["Central Silk Board", "Whitefield", "BTM Layout", "Peenya Industrial Area", "Hebbal", "City Railway Station"],
        "base_pm25": 36.0,
        "base_pm10": 78.0,
        "base_no2": 28.0,
        "base_so2": 10.0,
        "base_co": 0.85,
        "base_o3": 26.0,
        "base_admissions": 580,
        "winter_spike_factor": 1.25,
    },
    "Hyderabad": {
        "state": "Telangana",
        "tier": "Tier-1 Metro",
        "population_base": 10500000,
        "latitude": 17.3850,
        "longitude": 78.4867,
        "stations": ["Sanath Nagar", "Gachibowli IT Corridor", "Charminar Heritage Zone", "Kukatpally", "ICRISAT Patancheru", "Zoo Park"],
        "base_pm25": 44.0,
        "base_pm10": 92.0,
        "base_no2": 32.0,
        "base_so2": 12.0,
        "base_co": 0.95,
        "base_o3": 30.0,
        "base_admissions": 520,
        "winter_spike_factor": 1.35,
    },
    "Chennai": {
        "state": "Tamil Nadu",
        "tier": "Tier-1 Metro",
        "population_base": 11500000,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "stations": ["Alandur", "Manali Industrial Zone", "Velachery", "Kodungaiyur", "Arumbakkam"],
        "base_pm25": 42.0,
        "base_pm10": 85.0,
        "base_no2": 26.0,
        "base_so2": 11.0,
        "base_co": 0.9,
        "base_o3": 28.0,
        "base_admissions": 560,
        "winter_spike_factor": 1.20,
    },
    "Ahmedabad": {
        "state": "Gujarat",
        "tier": "Tier-1 Metro",
        "population_base": 8500000,
        "latitude": 23.0225,
        "longitude": 72.5714,
        "stations": ["Maninagar", "Vatva Industrial Area", "Rakhial", "Chandkheda", "Satellite"],
        "base_pm25": 65.0,
        "base_pm10": 135.0,
        "base_no2": 38.0,
        "base_so2": 22.0,
        "base_co": 1.15,
        "base_o3": 34.0,
        "base_admissions": 490,
        "winter_spike_factor": 1.60,
    },
    "Pune": {
        "state": "Maharashtra",
        "tier": "Tier-2 Metro",
        "population_base": 7200000,
        "latitude": 18.5204,
        "longitude": 73.8567,
        "stations": ["Shivajinagar", "Hinjewadi Tech Park", "Katraj", "Hadapsar", "Bhosari"],
        "base_pm25": 48.0,
        "base_pm10": 98.0,
        "base_no2": 30.0,
        "base_so2": 12.0,
        "base_co": 0.95,
        "base_o3": 31.0,
        "base_admissions": 430,
        "winter_spike_factor": 1.40,
    },
    "Lucknow": {
        "state": "Uttar Pradesh",
        "tier": "Tier-2 Metro",
        "population_base": 3800000,
        "latitude": 26.8467,
        "longitude": 80.9462,
        "stations": ["Lalbagh", "Talkatora", "Aliganj", "Gomti Nagar"],
        "base_pm25": 85.0,
        "base_pm10": 170.0,
        "base_no2": 44.0,
        "base_so2": 15.0,
        "base_co": 1.35,
        "base_o3": 36.0,
        "base_admissions": 380,
        "winter_spike_factor": 2.20,
    },
    "Patna": {
        "state": "Bihar",
        "tier": "Tier-2 Metro",
        "population_base": 2500000,
        "latitude": 25.5941,
        "longitude": 85.1376,
        "stations": ["Muradpur", "Samanpura", "DRM Office Danapur", "Rajbansi Nagar"],
        "base_pm25": 92.0,
        "base_pm10": 185.0,
        "base_no2": 45.0,
        "base_so2": 16.0,
        "base_co": 1.40,
        "base_o3": 37.0,
        "base_admissions": 340,
        "winter_spike_factor": 2.30,
    }
}

# CPCB & WHO Ambient Air Quality Standards & Breakpoints
POLLUTANT_THRESHOLDS = {
    "PM2.5": {
        "unit": "ug/m3",
        "good": 30,
        "satisfactory": 60,
        "moderate": 90,
        "poor": 120,
        "very_poor": 250,
        "severe": 380,
        "weight": 0.35,
    },
    "PM10": {
        "unit": "ug/m3",
        "good": 50,
        "satisfactory": 100,
        "moderate": 250,
        "poor": 350,
        "very_poor": 430,
        "severe": 550,
        "weight": 0.25,
    },
    "NO2": {
        "unit": "ug/m3",
        "good": 40,
        "satisfactory": 80,
        "moderate": 180,
        "poor": 280,
        "very_poor": 400,
        "severe": 500,
        "weight": 0.15,
    },
    "SO2": {
        "unit": "ug/m3",
        "good": 40,
        "satisfactory": 80,
        "moderate": 380,
        "poor": 800,
        "very_poor": 1600,
        "severe": 2000,
        "weight": 0.10,
    },
    "CO": {
        "unit": "mg/m3",
        "good": 1.0,
        "satisfactory": 2.0,
        "moderate": 10.0,
        "poor": 17.0,
        "very_poor": 34.0,
        "severe": 45.0,
        "weight": 0.05,
    },
    "O3": {
        "unit": "ug/m3",
        "good": 50,
        "satisfactory": 100,
        "moderate": 168,
        "poor": 208,
        "very_poor": 748,
        "severe": 850,
        "weight": 0.10,
    }
}

# AQI Risk Banding Definitions
AQI_BANDS = [
    {"name": "Good", "min": 0, "max": 50, "color": "#00E400", "description": "Minimal health impact"},
    {"name": "Satisfactory", "min": 51, "max": 100, "color": "#92D050", "description": "Minor breathing discomfort to sensitive people"},
    {"name": "Moderate", "min": 101, "max": 200, "color": "#FFFF00", "description": "Breathing discomfort with lung disease, asthma, heart diseases"},
    {"name": "Poor", "min": 201, "max": 300, "color": "#FF7E00", "description": "Breathing discomfort to most people on prolonged exposure"},
    {"name": "Very Poor", "min": 301, "max": 400, "color": "#FF0000", "description": "Respiratory illness to people on prolonged exposure"},
    {"name": "Severe", "min": 401, "max": 500, "color": "#7E0023", "description": "Respiratory effects even on healthy people; serious impact on diseases"}
]

# Admission Categories
ADMISSION_TYPES = ["Total_Admissions", "Respiratory_Admissions", "Cardiac_Admissions", "Emergency_Cases"]

# Age Demographics
AGE_GROUPS = ["Pediatric_Admissions", "Adult_Admissions", "Geriatric_Admissions"]

# Date Range: 4 Full Years (2022-01-01 to 2025-12-31 = 1,461 days)
START_DATE = "2022-01-01"
END_DATE = "2025-12-31"

# Maximum Lag in Days for Distributed Lag Analysis
MAX_LAG_DAYS = 14
