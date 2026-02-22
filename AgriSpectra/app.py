# =====================================================
# AgriSpectra - Flask Backend
# Scientific Crop Storage Risk Assessment System
# =====================================================

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
from urllib.parse import quote_plus
from urllib.request import urlopen
import data
import risk_engine
import eligibility_engine

app = Flask(__name__, template_folder="templates", static_folder="static")


AVAILABLE_CROPS = [
    'Wheat','Paddy','Rice','Mustard','Sugarcane','Black Pepper','Coffee','Banana',
    'Potato','Onion','Groundnut','Bajra'
]

SEASONS = ['Summer','Monsoon','Winter','Post-harvest']


def _safe_float(value):
    try:
        if value is None or str(value).strip() == '':
            return None
        return float(value)
    except Exception:
        return None


def _infer_region_from_coordinates(lat, lon):
    lat_mid = 22.5
    lon_mid = 82.5
    if lat is None or lon is None:
        return 'North'
    if lat >= lat_mid and lon >= lon_mid:
        return 'North'
    if lat < lat_mid and lon >= lon_mid:
        return 'East'
    if lat < lat_mid and lon < lon_mid:
        return 'South'
    return 'West'


def _fetch_json(url):
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))


def _resolve_place_in_india(place_query):
    q = quote_plus(place_query)
    url = f'https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&country=IN&language=en&format=json'
    data_json = _fetch_json(url)
    results = data_json.get('results') or []
    if not results:
        return None
    best = results[0]
    return {
        'name': best.get('name') or place_query,
        'admin1': best.get('admin1') or '',
        'country': best.get('country') or 'India',
        'latitude': best.get('latitude'),
        'longitude': best.get('longitude'),
    }


def _ten_day_weather_average(lat, lon):
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        '&daily=temperature_2m_mean,relative_humidity_2m_mean'
        '&timezone=auto&forecast_days=10'
    )
    data_json = _fetch_json(url)
    daily = data_json.get('daily') or {}
    temps = [x for x in (daily.get('temperature_2m_mean') or []) if isinstance(x, (int, float))]
    humidities = [x for x in (daily.get('relative_humidity_2m_mean') or []) if isinstance(x, (int, float))]
    if not temps or not humidities:
        return None

    avg_temp = round(sum(temps) / len(temps), 1)
    avg_humidity = round(sum(humidities) / len(humidities), 1)
    return {
        'avg_temperature': avg_temp,
        'avg_humidity': avg_humidity,
        'days_used': min(len(temps), len(humidities)),
    }


def _weather_hazard_alerts(lat, lon):
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        '&daily=time,precipitation_sum,windspeed_10m_max,weathercode'
        '&timezone=auto&forecast_days=7'
    )
    data_json = _fetch_json(url)
    daily = data_json.get('daily') or {}
    days = daily.get('time') or []
    precipitation = daily.get('precipitation_sum') or []
    wind_max = daily.get('windspeed_10m_max') or []
    weather_codes = daily.get('weathercode') or []

    alerts = []
    for idx, day in enumerate(days):
        rain = precipitation[idx] if idx < len(precipitation) else 0
        wind = wind_max[idx] if idx < len(wind_max) else 0
        code = weather_codes[idx] if idx < len(weather_codes) else None

        is_heavy_rain = isinstance(rain, (int, float)) and rain >= 50
        is_cyclone_like = (
            isinstance(wind, (int, float)) and wind >= 62
        ) or (code in {95, 96, 99})

        if is_heavy_rain:
            severity = 'SEVERE' if rain >= 100 else 'HIGH'
            alerts.append(
                {
                    'date': day,
                    'type': 'HEAVY_RAIN',
                    'severity': severity,
                    'headline': f'Heavy rain expected on {day}',
                    'details': f'Forecast rainfall is about {round(float(rain), 1)} mm.',
                    'recommendations': [
                        'Move produce to elevated and covered storage immediately.',
                        'Use waterproof tarpaulins and seal side openings to avoid moisture ingress.',
                        'Keep pallets above floor level and maintain drainage around storage.',
                    ],
                }
            )

        if is_cyclone_like:
            alerts.append(
                {
                    'date': day,
                    'type': 'CYCLONE_RISK',
                    'severity': 'SEVERE',
                    'headline': f'Cyclone/strong storm risk on {day}',
                    'details': f'Peak wind may reach about {round(float(wind), 1)} km/h.',
                    'recommendations': [
                        'Shift stock to the safest available pucca storage building.',
                        'Avoid temporary sheds; secure doors, roof sheets, and ventilation shutters.',
                        'Keep emergency backup: tarpaulins, ropes, power backup, and contact list.',
                    ],
                }
            )

    return {
        'alerts': alerts,
        'forecast_days_checked': len(days),
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    result = None
    eligibility_result = None
    form = {}
    if request.method == 'POST':
        form = {
            'crop_type': request.form.get('crop_type'),
            'place': request.form.get('place'),
            'latitude': request.form.get('latitude'),
            'longitude': request.form.get('longitude'),
            'temperature': request.form.get('temperature'),
            'humidity': request.form.get('humidity'),
            'season': request.form.get('season'),
            'storage_days': request.form.get('storage_days')
        }
        lat = _safe_float(form.get('latitude'))
        lon = _safe_float(form.get('longitude'))
        form['region'] = _infer_region_from_coordinates(lat, lon)
        result = risk_engine.compute_risk(form)
        eligibility_payload = dict(form)
        eligibility_payload['risk_level'] = result.get('risk_level')
        eligibility_result = eligibility_engine.evaluate_eligibility(eligibility_payload)
    return render_template(
        'calculator.html',
        crops=AVAILABLE_CROPS,
        seasons=SEASONS,
        result=result,
        eligibility_result=eligibility_result,
        form=form
    )


@app.route('/how')
def how():
    return render_template('how.html')


@app.route('/data-source')
def data_source():
    return render_template('data.html')


@app.route('/government-support')
def government_support():
    return render_template('government_support.html')


@app.route('/eligibility-checker')
def eligibility_checker():
    return redirect(url_for('calculator'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/api/risk', methods=['POST'])
def api_risk():
    params = request.get_json() or {}
    if not params.get('region'):
        lat = _safe_float(params.get('latitude'))
        lon = _safe_float(params.get('longitude'))
        params['region'] = _infer_region_from_coordinates(lat, lon)
    res = risk_engine.compute_risk(params)
    return jsonify(res)


@app.route('/api/eligibility', methods=['POST'])
def api_eligibility():
    params = request.get_json() or {}
    if not params.get('region'):
        lat = _safe_float(params.get('latitude'))
        lon = _safe_float(params.get('longitude'))
        params['region'] = _infer_region_from_coordinates(lat, lon)
    risk_level = (params.get('risk_level') or '').strip()

    if not risk_level:
        risk_payload = {
            'crop_type': params.get('crop_type'),
            'region': params.get('region'),
            'temperature': params.get('temperature'),
            'humidity': params.get('humidity'),
            'season': params.get('season'),
            'storage_days': params.get('storage_days'),
        }
        risk_res = risk_engine.compute_risk(risk_payload)
        risk_level = risk_res.get('risk_level') or risk_res.get('risk_level'.lower()) or 'UNKNOWN'
        params['risk_level'] = risk_level

    res = eligibility_engine.evaluate_eligibility(params)
    return jsonify(res)


@app.route('/api/weather-average', methods=['POST'])
def api_weather_average():
    params = request.get_json() or {}
    place = (params.get('place') or '').strip()
    lat = _safe_float(params.get('latitude'))
    lon = _safe_float(params.get('longitude'))
    resolved_place = None

    if lat is None or lon is None:
        if not place:
            return jsonify({'error': 'Please provide a place in India or valid coordinates.'}), 400
        resolved_place = _resolve_place_in_india(place)
        if not resolved_place:
            return jsonify({'error': 'Place not found in India. Please refine your input.'}), 404
        lat = _safe_float(resolved_place.get('latitude'))
        lon = _safe_float(resolved_place.get('longitude'))

    try:
        weather = _ten_day_weather_average(lat, lon)
    except Exception:
        return jsonify({'error': 'Unable to fetch weather right now. Please enter values manually.'}), 502

    if not weather:
        return jsonify({'error': 'Weather data unavailable for this location.'}), 404

    region = _infer_region_from_coordinates(lat, lon)
    place_name = place
    if resolved_place:
        place_name = ', '.join(
            [x for x in [resolved_place.get('name'), resolved_place.get('admin1'), resolved_place.get('country')] if x]
        )

    return jsonify(
        {
            'place': place_name,
            'latitude': lat,
            'longitude': lon,
            'region': region,
            **weather,
        }
    )


@app.route('/api/weather-alerts', methods=['POST'])
def api_weather_alerts():
    params = request.get_json() or {}
    place = (params.get('place') or '').strip()
    lat = _safe_float(params.get('latitude'))
    lon = _safe_float(params.get('longitude'))
    resolved_place = None

    if lat is None or lon is None:
        if not place:
            return jsonify({'error': 'Please provide a place in India or valid coordinates.'}), 400
        resolved_place = _resolve_place_in_india(place)
        if not resolved_place:
            return jsonify({'error': 'Place not found in India. Please refine your input.'}), 404
        lat = _safe_float(resolved_place.get('latitude'))
        lon = _safe_float(resolved_place.get('longitude'))

    try:
        hazards = _weather_hazard_alerts(lat, lon)
    except Exception:
        return jsonify({'error': 'Unable to fetch hazard alerts right now.'}), 502

    place_name = place
    if resolved_place:
        place_name = ', '.join(
            [x for x in [resolved_place.get('name'), resolved_place.get('admin1'), resolved_place.get('country')] if x]
        )

    return jsonify(
        {
            'place': place_name,
            'latitude': lat,
            'longitude': lon,
            **hazards,
        }
    )


if __name__ == '__main__':
    # listen on all interfaces so Docker/container networks can access the app
    app.run(host='0.0.0.0', debug=True)
