"""
app.py — SolarSmart Flask Backend (Residential Edition)

Home profiles (Vijayawada rooftop norms):
  1BHK: 1.0 kWp system, ~150 kWh/month consumption
  2BHK: 2.0 kWp system, ~250 kWh/month consumption
  3BHK: 3.0 kWp system, ~400 kWh/month consumption

Calculation logic:
  efficiency      = ML model output (0.0–1.0)
  actual_kw       = efficiency × system_kWp
  daily_kwh       = actual_kw × peak_sun_hours  (5h for Vijayawada)
  monthly_gen     = daily_kwh × 30
  offset_kwh      = min(monthly_gen, monthly_consumption)
  savings         = offset_kwh × tariff
  remaining_bill  = (monthly_consumption - offset_kwh) × tariff
"""

from flask import Flask, render_template, request, jsonify
from model import predict_efficiency, get_model_metrics, train_model
from database import init_db, save_prediction, get_history
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder='templates', static_folder='static')

TARIFF       = 7.5   # ₹/kWh APSPDCL domestic
CO2_PER_KWH  = 0.82  # kg CO2 per kWh (India grid)
PEAK_SUN_HRS = 5.0   # Vijayawada average peak sun hours/day
TREE_KG_YR   = 21.7  # kg CO2 absorbed per tree per year

HOME_PROFILES = {
    '1bhk': {'label': '1 BHK',  'capacity_kwp': 1.0, 'monthly_kwh': 150},
    '2bhk': {'label': '2 BHK',  'capacity_kwp': 2.0, 'monthly_kwh': 250},
    '3bhk': {'label': '3 BHK',  'capacity_kwp': 3.0, 'monthly_kwh': 400},
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        temp      = float(request.form['temperature'])
        humidity  = float(request.form['humidity'])
        wind      = float(request.form['windspeed'])
        irrad     = float(request.form['irradiance'])
        home_type = request.form.get('home_type', '2bhk').lower()

        if home_type not in HOME_PROFILES:
            home_type = '2bhk'

        profile     = HOME_PROFILES[home_type]
        capacity    = profile['capacity_kwp']
        monthly_use = profile['monthly_kwh']

        # ── ML prediction ──
        efficiency = predict_efficiency(temp, humidity, wind, irrad)
        actual_kw  = efficiency * capacity           # real output in kW

        # ── Energy calculations ──
        daily_kwh    = actual_kw * PEAK_SUN_HRS      # kWh per day
        monthly_gen  = daily_kwh * 30                # kWh generated per month

        # How much of consumption is covered by solar
        offset_kwh   = min(monthly_gen, monthly_use)
        cover_pct    = round((offset_kwh / monthly_use) * 100, 1)

        # Bills
        normal_bill  = monthly_use * TARIFF
        remaining    = (monthly_use - offset_kwh) * TARIFF
        savings_mo   = offset_kwh * TARIFF
        savings_yr   = savings_mo * 12

        # CO2
        co2_monthly  = offset_kwh * CO2_PER_KWH
        trees_equiv  = round(co2_monthly / (TREE_KG_YR / 12), 1)

        # ── Panel tilt recommendation ──
        base_tilt  = 16.5  # Vijayawada latitude
        temp_adj   = (temp - 25) * 0.3
        tilt_angle = round(max(10, min(35, base_tilt + temp_adj)), 1)

        # ── Best usage window ──
        if irrad > 700:
            best_time = "10 AM – 2 PM"
            time_desc = "Peak generation window"
        elif irrad > 400:
            best_time = "9 AM – 3 PM"
            time_desc = "Moderate generation window"
        else:
            best_time = "11 AM – 1 PM"
            time_desc = "Low irradiance — limited output"

        # ── Efficiency tip ──
        if humidity > 80:
            tip = "High humidity detected. Clean your panels regularly to avoid soiling losses."
        elif temp > 40:
            tip = "High temperature reduces efficiency ~0.4%/°C above 25°C. Ensure good ventilation behind panels."
        elif wind > 20:
            tip = "Strong winds are cooling your panels — efficiency is slightly above average today."
        elif irrad < 200:
            tip = "Low irradiance today. Consider scheduling high-energy appliances for a sunnier day."
        else:
            tip = "Good conditions. Keep panels clean and unshaded for optimal output."

        save_prediction(temp, humidity, wind, irrad, actual_kw,
                        savings_mo, co2_monthly, home_type)

        return jsonify({
            'efficiency_pct':  round(efficiency * 100, 1),
            'actual_kw':       round(actual_kw, 3),
            'daily_kwh':       round(daily_kwh, 2),
            'monthly_gen':     round(monthly_gen, 1),
            'monthly_use':     monthly_use,
            'offset_kwh':      round(offset_kwh, 1),
            'cover_pct':       cover_pct,
            'normal_bill':     round(normal_bill, 0),
            'remaining_bill':  round(remaining, 0),
            'savings_monthly': round(savings_mo, 0),
            'savings_yearly':  round(savings_yr, 0),
            'co2_monthly':     round(co2_monthly, 1),
            'trees_equiv':     trees_equiv,
            'tilt_angle':      tilt_angle,
            'best_time':       best_time,
            'time_desc':       time_desc,
            'efficiency_tip':  tip,
            'capacity_kwp':    capacity,
            'home_label':      profile['label'],
        })

    except ValueError as e:
        return jsonify({'error': f'Invalid input: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/metrics')
def metrics():
    try:
        return jsonify(get_model_metrics())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/history')
def history():
    try:
        rows = get_history(20)
        keys = ['id','timestamp','temperature','humidity','windspeed',
                'irradiance','actual_kw','savings_monthly','co2_reduction','home_type']
        return jsonify([dict(zip(keys, r)) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    for d in ['models','data','templates','static/css','static/js']:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
    init_db()
    train_model()
    print("SolarSmart running at http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)