# =====================================================
# AgriSpectra - Rule-Based Crop Storage Risk Engine
# =====================================================

"""Rule-based risk engine for post-harvest storage.

Provides `compute_risk(params)` which accepts a params dict, and a
backwards-compatible `calculate_risk(...)` wrapper that accepts explicit
arguments (crop_type, region, temperature, humidity, season, storage_days).
"""















"""Rule-based risk engine for post-harvest storage.

Inputs expected (dict):
- crop_type: string
- region: one of 'North','South','East','West'
- temperature: float (°C)
- humidity: float (%%)
- season: 'Summer'|'Monsoon'|'Winter'|'Post-harvest'
- storage_days: int

Outputs:
- risk_score: 0-100
- risk_level: SAFE/MODERATE/HIGH/CRITICAL
- explanation: text with reasons
- recommendations: list of actions
"""

from math import fabs


# Base crop thresholds (example values refined for Indian regions)
CROPS = {
    'wheat': {
        'ideal_temp': (25, 30),
        'ideal_humidity': (30, 45),
        'storage_days_safe': 365,
        'respiration': 'low',
        'notes': 'Low moisture grain; fungal risk increases if RH > 60%.'
    },
    'paddy': {
        'ideal_temp': (20, 30),
        'ideal_humidity': (65, 80),
        'storage_days_safe': 180,
        'respiration': 'medium',
        'notes': 'Mold risk increases rapidly above 80% RH.'
    },
    'mustard': {
        'ideal_temp': (20, 30),
        'ideal_humidity': (40, 55),
        'storage_days_safe': 270,
        'respiration': 'low',
        'notes': 'Oilseed; sensitive to humidity.'
    },
    'sugarcane': {
        'ideal_temp': (28, 35),
        'ideal_humidity': (60, 85),
        'storage_days_safe': 3,
        'respiration': 'very_high',
        'notes': 'Very high respiration rate — spoils rapidly.'
    },
    'black pepper': {
        'ideal_temp': (20, 30),
        'ideal_humidity': (60, 75),
        'storage_days_safe': 365,
        'respiration': 'low',
        'notes': 'Above 75% RH → aflatoxin risk.'
    },
    'coffee': {
        'ideal_temp': (15, 25),
        'ideal_humidity': (50, 65),
        'storage_days_safe': 365,
        'respiration': 'low',
        'notes': 'Needs dry, ventilated storage.'
    },
    'banana': {
        'ideal_temp': (13, 15),
        'ideal_humidity': (85, 95),
        'storage_days_safe': 10,
        'respiration': 'very_high',
        'notes': 'Climacteric fruit — ethylene and rapid ripening.'
    },
    'potato': {
        'ideal_temp': (10, 15),
        'ideal_humidity': (85, 90),
        'storage_days_safe': 60,
        'respiration': 'medium',
        'notes': 'High temp causes sprouting.'
    },
    'onion': {
        'ideal_temp': (25, 35),
        'ideal_humidity': (40, 60),
        'storage_days_safe': 180,
        'respiration': 'low',
        'notes': 'Sprouting if humidity rises.'
    },
    'groundnut': {
        'ideal_temp': (20, 30),
        'ideal_humidity': (30, 50),
        'storage_days_safe': 365,
        'respiration': 'low',
        'notes': 'Aflatoxin risk if RH > 70%.'
    },
    'bajra': {
        'ideal_temp': (15, 30),
        'ideal_humidity': (30, 50),
        'storage_days_safe': 365,
        'respiration': 'low',
        'notes': 'Highly storage-stable grain.'
    }
}

# Alias 'rice' to 'paddy' (user-facing "Rice" maps to internal 'paddy' rules)
if 'paddy' in CROPS:
    CROPS['rice'] = CROPS['paddy']


REGION_ADJUSTMENTS = {
    'North': {'humidity_bias': -5, 'temp_bias': 0},
    'South': {'humidity_bias': +3, 'temp_bias': +1},
    'East': {'humidity_bias': +5, 'temp_bias': +1},
    'West': {'humidity_bias': -2, 'temp_bias': +2}
}


RESPIRATION_FACTOR = {
    'low': 0.9,
    'medium': 1.0,
    'high': 1.2,
    'very_high': 1.5
}


def clamp(v, a, b):
    return max(a, min(b, v))


def compute_risk(params):
    # normalize inputs
    crop = (params.get('crop_type') or '').lower()
    region = params.get('region') or 'North'
    try:
        temp = float(params.get('temperature') or 0.0)
    except Exception:
        temp = 0.0
    try:
        rh = float(params.get('humidity') or 0.0)
    except Exception:
        rh = 0.0
    season = params.get('season') or 'Post-harvest'
    try:
        days = int(params.get('storage_days') or 0)
    except Exception:
        days = 0

    explanation = []
    recommendations = []

    # Accept common user typo 'rise' as 'rice'
    if crop == 'rise':
        crop = 'rice'

    # Special Rice/Paddy evaluation using user-provided rules
    if crop in ('rice', 'paddy'):
        # Inputs already normalized to temp, rh, days, season
        s = (season or '').lower()
        # Humidity score (0-100) - highest impact
        if rh <= 65:
            hum_score = 0.0
            hum_label = 'Safe humidity (≤65%)'
        elif 66 <= rh <= 75:
            hum_score = 50.0
            hum_label = 'Moderate humidity (66–75%)'
        else:
            hum_score = 100.0
            hum_label = 'High humidity (>75%) — fungal/mold risk'

        # Temperature score
        if temp <= 25:
            temp_score = 0.0
            temp_label = 'Safe temperature (≤25°C)'
        elif 26 <= temp <= 32:
            temp_score = 40.0
            temp_label = 'Moderate temperature (26–32°C)'
        else:
            temp_score = 80.0
            temp_label = 'High temperature (>32°C) — spoilage/insects'

        # Storage duration score
        if days <= 30:
            days_score = 0.0
            days_label = 'Short storage (≤30 days)'
        elif 31 <= days <= 90:
            days_score = 40.0
            days_label = 'Medium storage (31–90 days)'
        else:
            days_score = 80.0
            days_label = 'Long storage (>90 days) — quality loss'

        # Season multiplier
        if 'monsoon' in s or 'heavy' in s:
            season_mul = 1.15
            season_label = 'Monsoon/Heavy rainfall — high impact'
        elif 'moderate' in s or 'rain' in s:
            season_mul = 1.05
            season_label = 'Moderate rainfall — medium impact'
        else:
            season_mul = 0.95
            season_label = 'Dry/Winter — low impact'

        # Weights: humidity highest, then temperature, then duration
        w_hum = 0.5
        w_temp = 0.3
        w_days = 0.2

        combined = (hum_score * w_hum) + (temp_score * w_temp) + (days_score * w_days)
        combined = combined * season_mul
        risk_pct = clamp(round(combined, 1), 0.0, 100.0)

        # Risk level mapping per spec
        if risk_pct <= 30:
            level = 'Low'
            recommendation = 'Store as usual; monitor regularly.'
        elif risk_pct <= 60:
            level = 'Medium'
            recommendation = 'Monitor closely; consider selling part or improve storage.'
        else:
            level = 'High'
            recommendation = 'Sell now or move to controlled storage immediately.'

        # Farmer-friendly explanation
        explanation_text = f"{hum_label}. {temp_label}. {days_label}. {season_label}."

        return {
            'risk_percentage': risk_pct,
            'risk_level': level,
            'explanation': explanation_text,
            'recommendation': recommendation,
            'details': {
                'humidity': rh,
                'temperature': temp,
                'storage_days': days,
                'season': season
            }
        }

    if crop not in CROPS:
        # unknown crop: use conservative defaults
        base_safe_temp = (15, 30)
        base_safe_rh = (30, 70)
        safe_days = 90
        respiration = 'medium'
        notes = 'Unknown crop — using conservative defaults.'
    else:
        info = CROPS[crop]
        base_safe_temp = info['ideal_temp']
        base_safe_rh = info['ideal_humidity']
        safe_days = info['storage_days_safe']
        respiration = info['respiration']
        notes = info.get('notes', '')

    # apply regional adjustments
    adj = REGION_ADJUSTMENTS.get(region, {'humidity_bias': 0, 'temp_bias': 0})
    ideal_temp = (base_safe_temp[0] + adj['temp_bias'], base_safe_temp[1] + adj['temp_bias'])
    ideal_rh = (base_safe_rh[0] + adj['humidity_bias'], base_safe_rh[1] + adj['humidity_bias'])

    score = 0.0

    # Temperature factor: penalty when outside ideal range
    if temp < ideal_temp[0]:
        diff = ideal_temp[0] - temp
        temp_penalty = diff * 1.5
        explanation.append(f'Temperature {temp}°C below ideal range {ideal_temp[0]}–{ideal_temp[1]}°C.')
    elif temp > ideal_temp[1]:
        diff = temp - ideal_temp[1]
        temp_penalty = diff * 2.0
        explanation.append(f'Temperature {temp}°C above ideal range {ideal_temp[0]}–{ideal_temp[1]}°C.')
    else:
        temp_penalty = 0.0
        explanation.append(f'Temperature {temp}°C within ideal range.')

    score += temp_penalty

    # Humidity factor
    if rh < ideal_rh[0]:
        diff = ideal_rh[0] - rh
        rh_penalty = diff * 1.2
        explanation.append(f'Humidity {rh}% below ideal range {ideal_rh[0]}–{ideal_rh[1]}% (dry).')
    elif rh > ideal_rh[1]:
        diff = rh - ideal_rh[1]
        rh_penalty = diff * 2.5
        explanation.append(f'Humidity {rh}% above ideal range {ideal_rh[0]}–{ideal_rh[1]}% (wet).')
    else:
        rh_penalty = 0.0
        explanation.append(f'Humidity {rh}% within ideal range.')

    score += rh_penalty

    # Storage duration penalty
    if days <= safe_days:
        days_penalty = 0.0
        explanation.append(f'Storage duration {days} days within safe limit ({safe_days} days).')
    else:
        over = days - safe_days
        # penalize proportionally but cap
        days_penalty = min(30.0, over * 0.5)
        explanation.append(f'Storage duration {days} days exceeds safe limit ({safe_days} days) by {over} days.')

    score += days_penalty

    # Seasonal adjustments
    season = season.lower()
    if 'monsoon' in season:
        season_penalty = 12.0
        explanation.append('Season = Monsoon; raises risk due to high ambient moisture.')
    elif 'summer' in season:
        # humid summer vs dry summer depends on region/humidity
        if rh > 65:
            season_penalty = 10.0
            explanation.append('Humid summer conditions increase fungal/spoilage risk.')
        else:
            season_penalty = 2.0
            explanation.append('Summer season with moderate humidity.')
    elif 'post-harvest' in season:
        season_penalty = 3.0
        explanation.append('Post-harvest handling affects risk depending on storage readiness.')
    else:
        season_penalty = 0.0
        explanation.append('Seasonal effect minimal.')

    score += season_penalty

    # Respiration / crop sensitivity multiplier
    resp_factor = RESPIRATION_FACTOR.get(respiration, 1.0)
    if resp_factor > 1.0:
        explanation.append(f'Crop respiration rate {respiration} increases spoilage risk.')

    score *= resp_factor

    # Special critical checks (e.g., sugarcane, banana)
    if crop in ['sugarcane', 'banana']:
        # extremely sensitive: if storage days > safe by even small amount, escalate
        if days > safe_days:
            score += 20.0
            explanation.append('Highly perishable crop: rapid risk escalation when stored beyond safe duration.')

    # Caps and normalization to 0-100
    raw_score = clamp(score, 0.0, 100.0)
    # Round for readability
    risk_score = round(raw_score, 1)

    # Risk level mapping
    if risk_score <= 20:
        level = 'SAFE'
    elif risk_score <= 50:
        level = 'MODERATE'
    elif risk_score <= 80:
        level = 'HIGH'
    else:
        level = 'CRITICAL'

    # Build human explanation and recommendations
    explanation_text = notes + ' ' + ' '.join(explanation)

    if level == 'SAFE':
        recommendations.append('Maintain current storage conditions; monitor weekly.')
    if level == 'MODERATE':
        recommendations.append('Consider ventilation and reduce humidity (use desiccants or drying).')
        recommendations.append('Check storage for early signs of mold or pests.')
    if level == 'HIGH':
        recommendations.append('Reduce storage temperature if possible; increase ventilation.')
        recommendations.append('Move to dryer storage or use moisture control measures.')
    if level == 'CRITICAL':
        recommendations.append('Immediate action: move produce to cold storage or sell/consume promptly.')
        recommendations.append('Use aeration, drying, or short-term processing to avoid loss.')

    # Tailored recommendations based on crop
    if crop in ['paddy', 'groundnut'] and rh > 70:
        recommendations.append('Dry grains to safe moisture content and avoid long storage during humid season.')

    return {
        'risk_score': risk_score,
        'risk_level': level,
        'explanation': explanation_text.strip(),
        'recommendations': recommendations,
        'details': {
            'ideal_temp': ideal_temp,
            'ideal_humidity': ideal_rh,
            'safe_days': safe_days,
            'respiration': respiration
        }
    }


def calculate_risk(crop_type, region, temperature, humidity, season, storage_days):
    """Backward-compatible wrapper: build params dict and call compute_risk."""
    params = {
        'crop_type': crop_type,
        'region': region,
        'temperature': temperature,
        'humidity': humidity,
        'season': season,
        'storage_days': storage_days
    }
    return compute_risk(params)