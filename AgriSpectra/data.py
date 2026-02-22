# =====================================================
# AgriSpectra - Scientific Crop Storage Threshold Data
# Source-inspired: ICAR, FAO, post-harvest research
# =====================================================


# -------------------------------
# Crop Thresholds by Region
# -------------------------------
CROP_DATA = {

    # 🌾 NORTH INDIA
    "North": {
        "wheat": {
            "temp": (25, 30),
            "humidity": (30, 45),
            "max_days": 365,
            "respiration": "low",
            "category": "grain",
            "notes": "Low moisture grain; fungal risk mainly if RH > 60%"
        },
        "paddy": {
            "temp": (20, 30),
            "humidity": (65, 80),
            "max_days": 180,
            "respiration": "medium",
            "category": "grain",
            "notes": "Mold risk increases rapidly above 80% RH"
        },
        "mustard": {
            "temp": (20, 30),
            "humidity": (40, 55),
            "max_days": 270,
            "respiration": "low",
            "category": "oilseed",
            "notes": "Oilseed sensitive to moisture absorption"
        },
        "sugarcane": {
            "temp": (28, 35),
            "humidity": (60, 85),
            "max_days": 3,
            "respiration": "very_high",
            "category": "perishable",
            "notes": "Very high respiration; rapid microbial spoilage"
        }
    },

    # 🌴 SOUTH INDIA
    "South": {
        "black_pepper": {
            "temp": (20, 30),
            "humidity": (60, 75),
            "max_days": 365,
            "respiration": "low",
            "category": "spice",
            "notes": "Above 75% RH → aflatoxin risk"
        },
        "coffee": {
            "temp": (15, 25),
            "humidity": (50, 65),
            "max_days": 365,
            "respiration": "low",
            "category": "beverage_crop",
            "notes": "Requires dry, ventilated storage"
        },
        "paddy": {
            "temp": (20, 30),
            "humidity": (65, 80),
            "max_days": 180,
            "respiration": "medium",
            "category": "grain",
            "notes": "High fungal risk in humid tropical climate"
        },
        "banana": {
            "temp": (13, 15),
            "humidity": (85, 95),
            "max_days": 10,
            "respiration": "very_high",
            "category": "fruit",
            "notes": "Climacteric fruit; ethylene-driven ripening"
        }
    },

    # 🌧 EAST INDIA
    "East": {
        "paddy": {
            "temp": (20, 30),
            "humidity": (65, 85),
            "max_days": 180,
            "respiration": "medium",
            "category": "grain",
            "notes": "Flood-prone regions increase moisture damage"
        },
        "potato": {
            "temp": (10, 15),
            "humidity": (85, 90),
            "max_days": 60,
            "respiration": "medium",
            "category": "tuber",
            "notes": "High temperature causes sprouting"
        },
        "jute": {
            "temp": (20, 35),
            "humidity": (70, 90),
            "max_days": 180,
            "respiration": "low",
            "category": "fiber",
            "notes": "Fiber weakens under excess moisture"
        },
        "turmeric": {
            "temp": (18, 30),
            "humidity": (40, 60),
            "max_days": 270,
            "respiration": "low",
            "category": "spice",
            "notes": "Dry storage prevents mold growth"
        }
    },

    # ☀️ WEST INDIA
    "West": {
        "onion": {
            "temp": (25, 35),
            "humidity": (40, 60),
            "max_days": 180,
            "respiration": "medium",
            "category": "vegetable",
            "notes": "Sprouting and rotting if humidity rises"
        },
        "groundnut": {
            "temp": (20, 30),
            "humidity": (30, 50),
            "max_days": 365,
            "respiration": "low",
            "category": "oilseed",
            "notes": "Aflatoxin risk if RH > 70%"
        },
        "cotton": {
            "temp": (20, 35),
            "humidity": (20, 50),
            "max_days": 365,
            "respiration": "none",
            "category": "fiber",
            "notes": "Fiber absorbs moisture; quality degrades"
        },
        "bajra": {
            "temp": (15, 30),
            "humidity": (30, 50),
            "max_days": 365,
            "respiration": "low",
            "category": "grain",
            "notes": "Highly storage-stable millet crop"
        }
    }
}


# -------------------------------
# Seasonal Risk Modifiers
# -------------------------------
SEASON_RISK = {
    "Summer": 10,
    "Monsoon": 25,
    "Winter": 5,
    "Post-harvest": 15
}


# -------------------------------
# Respiration Risk Multipliers
# -------------------------------
RESPIRATION_RISK = {
    "none": 0,
    "low": 5,
    "medium": 10,
    "high": 15,
    "very_high": 20
}