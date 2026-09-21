import pandas as pd
import serial
import time
import csv
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
FILE_NAME = "AQI_Prediction_IoT_50.csv"
ESP_PORT = "/dev/tty.usbserial-0001"  # <--- PASTE YOUR PORT HERE AGAIN

# --- PART 1: TRAIN MODEL ---
print("Training ML Model...")
try:
    data = pd.read_csv(FILE_NAME)
    data.columns = ['Temp', 'Hum', 'PM25', 'PM10', 'CO', 'NO2', 'SO2', 'O3', 'AQI']
    X = data[['Temp', 'Hum', 'PM25', 'PM10', 'CO', 'NO2', 'SO2', 'O3']]
    y = data['AQI']
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    print("Model Trained Successfully.")
except Exception as e:
    print(f"Error: {e}")
    exit()

# --- PART 2: SETUP LOGGING ---
csv_file = "aqi_history.csv"
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Temp", "Hum", "PM25", "CO", "AQI", "Status"])

# --- PART 3: LISTEN & LOG ---
print(f"Listening on {ESP_PORT} and saving to '{csv_file}'...")

try:
    ser = serial.Serial(ESP_PORT, 9600, timeout=1)
    time.sleep(2)

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line or "MQ" in line: continue

            values = line.split(',')
            if len(values) == 8:
                try:
                    sensor_data = {
                        'Temp': float(values[0]), 'Hum': float(values[1]),
                        'PM25': float(values[2]), 'PM10': float(values[3]),
                        'CO': float(values[4]), 'NO2': float(values[5]),
                        'SO2': float(values[6]), 'O3': float(values[7])
                    }

                    # Predict
                    input_df = pd.DataFrame([sensor_data])
                    predicted_aqi = rf_model.predict(input_df)[0]

                    # Status
                    if predicted_aqi <= 50: status = "Good"
                    elif predicted_aqi <= 100: status = "Moderate"
                    else: status = "Unhealthy"

                    # Print to Screen
                    print(f"Time: {datetime.now().strftime('%H:%M:%S')} | "
                          f"AQI: {predicted_aqi:.2f} | {status}")

                    # Save to File
                    with open(csv_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            sensor_data['Temp'], sensor_data['Hum'],
                            sensor_data['PM25'], sensor_data['CO'],
                            predicted_aqi, status
                        ])
                except ValueError:
                    pass

except KeyboardInterrupt:
    print("\nSaved data to aqi_history.csv. Exiting.")
