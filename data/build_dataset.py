"""
Build AQI_Prediction_IoT_50.csv for the AI-reinforced AQI sensor module.

Real data : daily CPCB (Central Pollution Control Board, India) records for Amritsar,
            taken from the public "city_day.csv" air-quality file (2017-2020).
            Columns used: PM2.5, PM10, CO, NO2, SO2, O3 and the reported AQI.
Synthetic : Temp and Hum. The CPCB file has no weather columns, so they are generated
            from approximate monthly climate normals for Amritsar plus day-to-day noise,
            then rounded/clipped to the DHT11's resolution and range.
            THEY ARE NOT MEASURED VALUES. Replace them with real weather for the same
            dates (see the Date column in AQI_Prediction_IoT_50_provenance.csv) if you can.

Output    : AQI_Prediction_IoT_50.csv (exactly what host/aqi_host.py expects):
            Temp, Hum, PM25, PM10, CO, NO2, SO2, O3, AQI
            Units: degC, %RH, ug/m3, ug/m3, mg/m3, ug/m3, ug/m3, ug/m3, CPCB AQI.

Usage     : python build_dataset.py            (needs internet + pandas, numpy)
            python build_dataset.py path/to/city_day.csv   (use a local copy instead)
"""
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_URL = ("https://raw.githubusercontent.com/vimalraj-76/"
              "An-algorithmic-approach-for-pollution-monitoring-and-predicting/main/cityday.csv")
CITY = "Amritsar"
SEED = 42
OUT_DIR = Path(__file__).resolve().parent

POLLUTANTS = ["PM2.5", "PM10", "CO", "NO2", "SO2", "O3"]

# Approximate monthly means for Amritsar (daily mean temperature in degC, relative humidity in %).
MONTH_TEMP = {1: 12.6, 2: 15.4, 3: 20.3, 4: 26.3, 5: 31.3, 6: 33.3,
              7: 31.2, 8: 30.2, 9: 28.6, 10: 24.2, 11: 18.4, 12: 13.6}
MONTH_RH = {1: 77, 2: 70, 3: 60, 4: 46, 5: 41, 6: 47,
            7: 71, 8: 77, 9: 68, 10: 57, 11: 62, 12: 74}

# How many rows to draw from each AQI band (follows the real spread, but guarantees
# that the rare very-polluted days are represented). Total = 50.
BANDS = [(0, 50, 6), (51, 100, 16), (101, 200, 16), (201, 300, 8), (301, 500, 4)]


def load_raw(path=None):
    if path:
        raw = Path(path).read_bytes()
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as r:
            raw = r.read()
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%y")
    return df


def main():
    df = load_raw(sys.argv[1] if len(sys.argv) > 1 else None)
    df = df[df["City"] == CITY].dropna(subset=POLLUTANTS + ["AQI"]).copy()

    # keep readings inside a range a low-cost node could plausibly report (drops extreme outliers)
    df = df[(df["PM2.5"] <= 300) & (df["PM10"] <= 450) & (df["AQI"] <= 500)]
    # CPCB files contain some 0.00 placeholders (mostly CO); drop rows with any zero pollutant
    df = df[(df[POLLUTANTS] > 0).all(axis=1)]

    rng = np.random.default_rng(SEED)
    parts = []
    for lo, hi, n in BANDS:
        band = df[(df["AQI"] >= lo) & (df["AQI"] <= hi)]
        parts.append(band.sample(n=n, random_state=int(rng.integers(0, 10_000))))
    s = pd.concat(parts).sort_values("Date").reset_index(drop=True)

    # synthetic weather from monthly climate normals
    m = s["Date"].dt.month
    temp = m.map(MONTH_TEMP) + rng.normal(0, 2.5, len(s))
    hum = m.map(MONTH_RH) + rng.normal(0, 8.0, len(s))
    s["Temp"] = np.clip(np.round(temp), 0, 50)      # DHT11: 1 degC resolution, 0-50 degC
    s["Hum"] = np.clip(np.round(hum), 20, 90)       # DHT11: 1 %RH resolution, 20-90 %RH

    out = pd.DataFrame({
        "Temp": s["Temp"].round(1), "Hum": s["Hum"].round(1),
        "PM25": s["PM2.5"].round(2), "PM10": s["PM10"].round(2),
        "CO": s["CO"].round(2), "NO2": s["NO2"].round(2),
        "SO2": s["SO2"].round(2), "O3": s["O3"].round(2),
        "AQI": s["AQI"].round(0),
    })
    out.to_csv(OUT_DIR / "AQI_Prediction_IoT_50.csv", index=False)

    prov = out.copy()
    prov.insert(0, "Date", s["Date"].dt.strftime("%Y-%m-%d"))
    prov.insert(1, "City", CITY)
    prov.to_csv(OUT_DIR / "AQI_Prediction_IoT_50_provenance.csv", index=False)
    print(f"wrote {len(out)} rows to {OUT_DIR}")


if __name__ == "__main__":
    main()
