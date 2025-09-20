
#define BLYNK_TEMPLATE_ID "TMPL3GyeZpPP3"
#define BLYNK_TEMPLATE_NAME "Object Detection Logger"

#include "secrets.h" // create this from secrets.h.example and do NOT commit
#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

// If secrets.h is not provided, fall back to these (for local testing only)
#ifndef WIFI_SSID
char ssid[] = "RUBIX";
#else
char ssid[] = WIFI_SSID;
#endif

#ifndef WIFI_PASS
char pass[] = "12345678";
#else
char pass[] = WIFI_PASS;
#endif

#ifndef BLYNK_AUTH_TOKEN
char blynk_token[] = "Zaq0dkSF5TSxdJTFoizjkllaDV3Z3S5V";
#else
char blynk_token[] = BLYNK_AUTH_TOKEN;
#endif

BlynkTimer timer;

String detectionStatus = "No Data";
String detectionTime = "No Data";
String detectionLog = "";
bool dataChanged = false;

#define V0_TERMINAL V0
#define V1_STATUS V1
#define V2_TIMESTAMP V2

void setup() {
  // Set baud to 9600 to match Python serial default; you can change via .env/config
  Serial.begin(9600);
  delay(100);

  Blynk.begin(blynk_token, ssid, pass);

  Serial.println("ESP8266 is online and connected to Blynk!");

  timer.setInterval(1000L, sendDataToBlynk);
}

void sendDataToBlynk() {
  if (dataChanged) {
    Blynk.virtualWrite(V1_STATUS, detectionStatus);
    Blynk.virtualWrite(V2_TIMESTAMP, detectionTime);
    Blynk.virtualWrite(V0_TERMINAL, detectionLog);
    dataChanged = false;
    Serial.println("Blynk updated with new data.");
  }
}

void receiveSerialData() {
  static String inputBuffer = "";

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      inputBuffer.trim();
      processSerialData(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

void processSerialData(String data) {
  if (data.startsWith("STATUS:")) {
    String newStatus = data.substring(7);
    if (newStatus != detectionStatus) {
      detectionStatus = newStatus;
      dataChanged = true;
      Serial.println("Updated status: " + detectionStatus);
    }
  } else if (data.startsWith("TIME:")) {
    String newTime = data.substring(5);
    if (newTime != detectionTime) {
      detectionTime = newTime;
      dataChanged = true;
      Serial.println("Updated timestamp: " + detectionTime);
    }
  } else if (data.startsWith("LOG:")) {
    String newLogEntry = data.substring(4);
    detectionLog += newLogEntry + "\n";

    if (detectionLog.length() > 1024) {
      detectionLog = detectionLog.substring(detectionLog.length() - 1024);
    }

    dataChanged = true;
    Serial.println("Updated log: " + newLogEntry);
  }
}

void loop() {
  Blynk.run();
  timer.run();
  receiveSerialData();
}
