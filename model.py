"""
model.py — ML core for SolarSmart (Residential Edition)

The model predicts panel EFFICIENCY RATIO (0.0-1.0).
app.py multiplies by system capacity (kWp) to get realistic kW output.

Home system sizes (Vijayawada rooftop norms):
  1BHK = 1 kWp  (~150 units/month consumption)
  2BHK = 2 kWp  (~250 units/month consumption)
  3BHK = 3 kWp  (~400 units/month consumption)
"""
import os, json, warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

warnings.filterwarnings('ignore')

BASE_DIR     = Path(__file__).resolve().parent
DATA_PATH    = BASE_DIR / 'data' / 'spg.csv'
MODEL_DIR    = BASE_DIR / 'models'
METRICS_PATH = MODEL_DIR / 'metrics.json'

FEATURE_COLS = [
    'temperature2mabovegnd',
    'relativehumidity2mabovegnd',
    'windspeed10mabovegnd',
    'shortwaveradiationbackwards',
]
TARGET_COL = 'generatedpowerkw'


def _load_real_data():
    all_cols = [
        'temperature2mabovegnd','relativehumidity2mabovegnd',
        'meansealevelpressureMSL','totalprecipitationsfc',
        'snowfallamountsfc','totalcloudcoversfc','highcloudcoverhighcldlay',
        'mediumcloudcovermidcldlay','lowcloudcoverlowcldlay',
        'shortwaveradiationbackwards','windspeed10mabovegnd',
        'winddirection10mabovegnd','windspeed80mabovegnd',
        'winddirection80mabovegnd','windspeed900mb','winddirection900mb',
        'windgust10mabovegnd','angleofincidence','zenith','azimuth',
        'generatedpowerkw',
    ]
    df = pd.read_csv(str(DATA_PATH), header=None, skiprows=1,
                     names=all_cols[:21], usecols=range(min(21,len(all_cols))))
    for col in FEATURE_COLS + [TARGET_COL]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df[FEATURE_COLS + [TARGET_COL]].dropna()
    # Normalise to efficiency 0-1
    peak = df[TARGET_COL].quantile(0.95)
    if peak > 0:
        df['efficiency'] = (df[TARGET_COL] / peak).clip(0, 1)
    else:
        df['efficiency'] = 0.0
    print(f"Loaded {len(df)} rows, efficiency range "
          f"{df['efficiency'].min():.3f}-{df['efficiency'].max():.3f}")
    return df


def _generate_synthetic_data(n=5000):
    rng = np.random.default_rng(42)
    temp       = rng.uniform(18, 46, n)
    humidity   = rng.uniform(25, 95, n)
    windspeed  = rng.uniform(0,  30, n)
    irradiance = rng.uniform(0, 1000, n)
    base       = irradiance / 1000.0
    temp_loss  = 0.004 * np.maximum(0, temp - 25)
    hum_loss   = 0.0008 * humidity
    wind_gain  = 0.0003 * windspeed
    noise      = rng.normal(0, 0.015, n)
    eff        = np.clip(base - temp_loss - hum_loss + wind_gain + noise, 0, 1)
    return pd.DataFrame({
        'temperature2mabovegnd':       temp,
        'relativehumidity2mabovegnd':  humidity,
        'windspeed10mabovegnd':        windspeed,
        'shortwaveradiationbackwards': irradiance,
        'generatedpowerkw':            eff,
        'efficiency':                  eff,
    })


def load_data():
    if DATA_PATH.exists():
        try:
            df = _load_real_data()
            if len(df) > 50:
                return df
        except Exception as e:
            print(f"CSV error ({e}), using synthetic data.")
    print("Generating synthetic training data...")
    df = _generate_synthetic_data()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(DATA_PATH), index=False)
    return df


def train_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df     = load_data()
    target = 'efficiency' if 'efficiency' in df.columns else TARGET_COL
    X      = df[FEATURE_COLS].values
    y      = df[target].values
    X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

    sc = StandardScaler()
    lr = LinearRegression()
    lr.fit(sc.fit_transform(X_train), y_train)
    yp_lr   = lr.predict(sc.transform(X_test))
    r2_lr   = r2_score(y_test, yp_lr)
    mae_lr  = mean_absolute_error(y_test, yp_lr)
    mse_lr  = mean_squared_error(y_test, yp_lr)

    poly_pipe = Pipeline([('sc',StandardScaler()),
                          ('poly',PolynomialFeatures(degree=2,include_bias=False)),
                          ('lr',LinearRegression())])
    poly_pipe.fit(X_train, y_train)
    yp_poly  = poly_pipe.predict(X_test)
    r2_poly  = r2_score(y_test, yp_poly)
    mae_poly = mean_absolute_error(y_test, yp_poly)
    mse_poly = mean_squared_error(y_test, yp_poly)

    if r2_poly >= r2_lr:
        best = 'polynomial'
        joblib.dump(poly_pipe, str(MODEL_DIR/'solar_model.pkl'))
        joblib.dump(None,      str(MODEL_DIR/'scaler.pkl'))
    else:
        best = 'linear'
        joblib.dump(lr, str(MODEL_DIR/'solar_model.pkl'))
        joblib.dump(sc, str(MODEL_DIR/'scaler.pkl'))

    joblib.dump(FEATURE_COLS, str(MODEL_DIR/'features.pkl'))
    joblib.dump(best,         str(MODEL_DIR/'model_type.pkl'))

    metrics = {
        'linear':     {'r2':round(r2_lr,4),   'mae':round(mae_lr,4),
                       'mse':round(mse_lr,4),  'rmse':round(mse_lr**0.5,4)},
        'polynomial': {'r2':round(r2_poly,4),  'mae':round(mae_poly,4),
                       'mse':round(mse_poly,4),'rmse':round(mse_poly**0.5,4)},
        'best_model': best,
        'training_samples': len(X_train),
        'test_samples':     len(X_test),
        'features':         FEATURE_COLS,
    }
    with open(str(METRICS_PATH),'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Best model: {best} | R²={max(r2_lr,r2_poly):.4f}")
    return metrics


def predict_efficiency(temperature, humidity, windspeed, irradiance):
    """Returns efficiency ratio 0.0-1.0"""
    if not (MODEL_DIR/'solar_model.pkl').exists():
        train_model()
    model      = joblib.load(str(MODEL_DIR/'solar_model.pkl'))
    scaler     = joblib.load(str(MODEL_DIR/'scaler.pkl'))
    model_type = joblib.load(str(MODEL_DIR/'model_type.pkl'))
    X = np.array([[temperature, humidity, windspeed, irradiance]])
    if model_type == 'polynomial':
        eff = model.predict(X)[0]
    else:
        eff = model.predict(scaler.transform(X))[0]
    return float(np.clip(eff, 0.0, 1.0))


def get_model_metrics():
    if not METRICS_PATH.exists():
        return train_model()
    with open(str(METRICS_PATH)) as f:
        return json.load(f)


if __name__ == '__main__':
    m = train_model()
    print(json.dumps(m, indent=2))