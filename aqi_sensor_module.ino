#include <DHT.h>

// ----------------- Pin definitions (GPIO Mapping) -----------------
// We use direct GPIO numbers to avoid "D2 was not declared" errors.
#define MQ135_PIN A0       // Analog input (A0 is always A0)

// GPIO Mappings for NodeMCU:
// D1 = GPIO 5
// D2 = GPIO 4
// D4 = GPIO 2
// D6 = GPIO 12
// D7 = GPIO 13
#define MQ2_DO_PIN 13      // Was D7 (GPIO 13)
#define GREEN_LED 5        // Was D1 (GPIO 5)
#define RED_LED 2          // Was D4 (GPIO 2)
#define BUZZER 12          // Was D6 (GPIO 12)
#define DHTPIN 4           // Was D2 (GPIO 4)
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

// ----------------- Thresholds -----------------
int badAirAQI = 200;       // AQI above this => bad air

void setup() {
  Serial.begin(9600);
  pinMode(MQ2_DO_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER, LOW);

  dht.begin();
  delay(2000);
}

void loop() {
  // 1. --- READ SENSORS ---
  int mq135Raw = analogRead(MQ135_PIN);
  int local_aqi = map(mq135Raw, 0, 1023, 0, 500);

  int mq2Digital = digitalRead(MQ2_DO_PIN);
  bool smokeDetected = (mq2Digital == LOW);

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    humidity = 50.0;
    temperature = 25.0;
  }

  // 2. --- ALERTS ---
  bool badAir = (local_aqi > badAirAQI);

  if (smokeDetected || badAir) {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
    digitalWrite(BUZZER, HIGH);
  } else {
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);
    digitalWrite(BUZZER, LOW);
  }

  // 3. --- PREPARE & SEND DATA TO PYTHON ---
  float send_temp = temperature;
  float send_hum = humidity;

  // Proxy calculations for ML model
  float pollutionFactor = mq135Raw / 10.0;
  float send_pm25 = pollutionFactor * 1.5;
  float send_pm10 = pollutionFactor * 2.0;
  float send_co = mq135Raw / 100.0;
  float send_no2 = 20.0 + (pollutionFactor / 2);
  float send_so2 = 10.0 + (pollutionFactor / 3);
  float send_o3 = 30.0;

  // Send as CSV line
  Serial.print(send_temp); Serial.print(",");
  Serial.print(send_hum); Serial.print(",");
  Serial.print(send_pm25); Serial.print(",");
  Serial.print(send_pm10); Serial.print(",");
  Serial.print(send_co); Serial.print(",");
  Serial.print(send_no2); Serial.print(",");
  Serial.print(send_so2); Serial.print(",");
  Serial.println(send_o3);

  delay(2000);
}
