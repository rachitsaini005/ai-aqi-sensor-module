# Training dataset

`AQI_Prediction_IoT_50.csv` is the file `host/aqi_host.py` trains its Random Forest on.

## Format

50 rows, one header row, nine columns in this order (the host app renames columns by position, so the order matters):

| Column | Unit | Notes |
|---|---|---|
| `Temp` | °C | **synthetic**, whole degrees, 0–50 like the DHT11 |
| `Hum` | %RH | **synthetic**, whole percent, 20–90 like the DHT11 |
| `PM25` | µg/m³ | real (CPCB) |
| `PM10` | µg/m³ | real (CPCB) |
| `CO` | mg/m³ | real (CPCB); same scale as the firmware's `mq135Raw / 100` |
| `NO2` | µg/m³ | real (CPCB) |
| `SO2` | µg/m³ | real (CPCB) |
| `O3` | µg/m³ | real (CPCB) |
| `AQI` | CPCB AQI (0–500 scale) | real, as reported by CPCB (target variable) |

## Where the data comes from

- **Pollutants and AQI:** daily records for **Amritsar** from the public Indian CPCB air-quality file `city_day.csv` (2017–2020), fetched from this GitHub copy: [vimalraj-76/An-algorithmic-approach-for-pollution-monitoring-and-predicting](https://github.com/vimalraj-76/An-algorithmic-approach-for-pollution-monitoring-and-predicting). The underlying data is published by the Central Pollution Control Board, India. Check the original terms of use before redistributing it.
- **Temp and Hum:** the CPCB file has no weather columns, so these two are **generated**, not measured. Each is the approximate monthly mean for Amritsar plus random day-to-day noise (σ = 2.5 °C and 8 %RH), rounded and clipped to the DHT11's range and resolution. They follow the seasons but carry no real day-specific information.

## How the 50 rows were chosen

Days with a missing or zero pollutant value were dropped, as were extreme outliers (PM2.5 above 300, PM10 above 450). Rows were then drawn with a fixed seed from five AQI bands so that both clean and heavily polluted days appear:

| AQI band | Rows |
|---|---|
| 0–50 | 6 |
| 51–100 | 16 |
| 101–200 | 16 |
| 201–300 | 8 |
| 301–500 | 4 |

The result spans March 2017 to June 2020 and includes every calendar month (see the `Date` column in `AQI_Prediction_IoT_50_provenance.csv`).

## Files

- `AQI_Prediction_IoT_50.csv`: the training file.
- `AQI_Prediction_IoT_50_provenance.csv`: the same rows with `Date` and `City` added, so you can look up real weather for those days and replace `Temp` and `Hum`.
- `build_dataset.py`: rebuilds both files (`python build_dataset.py`; needs internet, `pandas` and `numpy`). Pass a local copy of `city_day.csv` as an argument to run offline.

## Sanity check

With the same training code as the host app, 5-fold cross-validation on this file gives R² ≈ 0.92 and a mean absolute error of about 18 AQI points. This is measured on days from a single city, so treat it as a smoke test, not as expected accuracy on the live module.

## Caveats

- The firmware only measures temperature and humidity directly. It sends the other six inputs as fixed functions of the single MQ-135 reading (see Table 5 in the report), and `O3` is always 30. The model was trained on independently measured pollutants, so live predictions are rough estimates. Feeding the firmware's formulas into the trained model gives an AQI that rises steadily with the MQ-135 reading (about 49 at ADC 80, 88 at 300, 195 at 600).
- The AQI here is the Indian CPCB index. The host app's labels (Good ≤ 50, Moderate ≤ 100, otherwise Unhealthy) are its own thresholds and do not match the CPCB category names.
- 50 rows is a small demonstration set. More rows, real weather data, or readings logged from the module itself (`aqi_history.csv`) would make the model more meaningful.
