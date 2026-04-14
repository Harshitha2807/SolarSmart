<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Exo+2&weight=800&size=40&duration=3000&pause=1000&color=F5A623&center=true&vCenter=true&width=600&lines=☀️+SolarSmart;AI-Powered+Solar+Intelligence" alt="SolarSmart" />

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-F5A623?style=for-the-badge&logo=python&logoColor=white&labelColor=0a0e1a"/>
  <img src="https://img.shields.io/badge/Flask-3.0-F5A623?style=for-the-badge&logo=flask&logoColor=white&labelColor=0a0e1a"/>
  <img src="https://img.shields.io/badge/scikit--learn-ML Model-F5A623?style=for-the-badge&logo=scikit-learn&logoColor=white&labelColor=0a0e1a"/>
  <img src="https://img.shields.io/badge/SQLite-Database-F5A623?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=0a0e1a"/>
  <img src="https://img.shields.io/badge/Chart.js-Visualisation-F5A623?style=for-the-badge&logo=chart.js&logoColor=white&labelColor=0a0e1a"/>
</p>

<p align="center">
  <strong>Know exactly how much solar power your home generates — and how much money you save.</strong><br/>
  A residential solar intelligence platform built for homeowners across India.
</p>

---

</div>

## ✨ What is SolarSmart?

**SolarSmart** is an AI-powered web application that predicts residential solar panel output using real-time weather inputs. It uses a machine learning model trained on **4,213 real solar generation records** to give homeowners accurate, actionable insights about their solar system.

> 🏆 Built for 1 BHK · 2 BHK · 3 BHK homes

---

## 🚀 Features

| Feature | Description |
|---|---|
| ⚡ **Real-time Prediction** | ML model predicts panel efficiency (0–1) from weather inputs |
| 💰 **Bill Calculator** | Shows monthly savings, remaining electricity bill & yearly estimate |
| 🌿 **Carbon Tracker** | CO₂ avoided & tree-equivalent months calculated per prediction |
| 📐 **Tilt Recommender** | Optimal panel tilt angle based on temperature & location |
| 🕐 **Usage Window** | Best time of day to run heavy appliances |
| 💡 **Smart Tips** | Condition-specific maintenance & efficiency advice |
| 🗂️ **History Log** | All predictions saved to SQLite with one-click clear |
| 🖥️ **Landing Page** | Polished intro page before the main dashboard |

---

## 🏠 Home Profiles

| Type | System Size | Monthly Consumption | Max Daily Output |
|------|------------|-------------------|-----------------|
| 🏠 1 BHK | 1 kWp | ~150 kWh/month | ~5 kWh/day |
| 🏡 2 BHK | 2 kWp | ~250 kWh/month | ~10 kWh/day |
| 🏘️ 3 BHK | 3 kWp | ~400 kWh/month | ~15 kWh/day |

---

## 🧠 How the ML Model Works

```
Weather Inputs  →  ML Model  →  Efficiency (0–1)  →  Calculations
─────────────────────────────────────────────────────────────────
Temperature       LinearReg      actual_kw           savings ₹
Humidity          PolyReg deg2   = eff × kWp         CO₂ kg
Wind Speed        (best chosen)  daily_kwh           bill offset
Irradiance                       = kw × peak hrs     trees equiv
```

- Trains both **Linear Regression** and **Polynomial Regression (degree 2)**
- Automatically picks the model with the higher R² score
- Falls back to synthetic data if no CSV is found
- Model metrics saved to `models/metrics.json`

---

## 📁 Project Structure

```
SolarSmart/
│
├── app.py              # Flask backend — all routes & calculations
├── model.py            # ML core — train, predict, metrics
├── database.py         # SQLite — save, fetch, clear predictions
│
├── templates/
│   ├── landing.html    # Intro / welcome page  (route: /)
│   └── index.html      # Main dashboard        (route: /app)
│
├── static/
│   ├── css/style.css   # Full dark-theme stylesheet
│   └── js/app.js       # Frontend logic & Chart.js
│
├── data/
│   ├── spg.csv         # Real solar generation dataset
│   └── predictions.db  # SQLite database (auto-created)
│
└── models/
    ├── solar_model.pkl # Trained model
    ├── scaler.pkl      # StandardScaler
    ├── features.pkl    # Feature column names
    ├── model_type.pkl  # "linear" or "polynomial"
    └── metrics.json    # R², MAE, RMSE scores
```

---

## ⚙️ Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/your-username/SolarSmart.git
cd SolarSmart
```

### 2. Install dependencies
```bash
pip install flask scikit-learn pandas numpy joblib
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

> The model trains automatically on first run. No setup needed.

---

## 🌐 API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Landing page |
| `GET` | `/app` | Main dashboard |
| `POST` | `/predict` | Run ML prediction |
| `GET` | `/history` | Fetch last 20 predictions |
| `POST` | `/clear-history` | Delete all saved predictions |
| `GET` | `/metrics` | Model performance metrics |

---

## 📊 Calculation Logic

```python
efficiency      = ML model output (0.0 – 1.0)
actual_kw       = efficiency × system_kWp
daily_kwh       = actual_kw × peak_sun_hours
monthly_gen     = daily_kwh × 30
offset_kwh      = min(monthly_gen, monthly_consumption)
savings_monthly = offset_kwh × tariff (₹/kWh)
co2_saved       = offset_kwh × 0.82 kg  (India grid factor)
```

---

## 🛠️ Tech Stack

<p>
  <img src="https://img.shields.io/badge/Python-Backend-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-Web Framework-000000?style=flat-square&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/scikit--learn-Machine Learning-F7931E?style=flat-square&logo=scikit-learn&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Chart.js-Charts-FF6384?style=flat-square&logo=chart.js&logoColor=white"/>
  <img src="https://img.shields.io/badge/HTML%2FCSS%2FJS-Frontend-F5A623?style=flat-square&logo=html5&logoColor=white"/>
</p>

---

## 📸 Screenshots

> Landing Page · Dashboard · History Tab · Model Info
>
> <img width="1870" height="879" alt="image" src="https://github.com/user-attachments/assets/b2e18569-26d8-457a-9d91-e64d9ea6ed16" />

<img width="1862" height="916" alt="Screenshot 2026-04-14 152121" src="https://github.com/user-attachments/assets/008b73d8-2e70-462b-b771-d82df0e01aea" />

<img width="1865" height="915" alt="Screenshot 2026-04-14 152141" src="https://github.com/user-attachments/assets/90b0b2cb-7bac-419b-b9ad-5da22506c208" />




## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

<div align="center">

Made with ☀️ for smarter solar decisions across India

**[⭐ Star this repo if you found it useful!](https://github.com/your-username/SolarSmart)**

</div>
