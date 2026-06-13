#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// --- 1. Network Configuration ---
const char* ssid = "Alkayyali-2.4G";          // Change to your Wi-Fi name
const char* password = "2001011521";  // Change to your Wi-Fi password

// *** CHANGE THIS before flashing: "track1" or "track2" ***
const char* TRACK = "track1";

const char* serverBase = "https://web-production-eadde.up.railway.app/api/";

// --- 2. Pin Definitions ---
const int START_BUTTON = 4;
const int STOP_BUTTON = 5;

void setup() {
  Serial.begin(115200);

  // Configure pins with internal pull-up resistors.
  // The pins will read HIGH normally, and LOW when the button connects them to GND.
  pinMode(START_BUTTON, INPUT_PULLUP);
  pinMode(STOP_BUTTON, INPUT_PULLUP);

  // Connect to the local Wi-Fi network
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected successfully!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}

void sendTrigger(String action) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure(); // Skip SSL certificate verification
    HTTPClient http;

    String fullUrl = String(serverBase) + TRACK + "/" + action + "/";
    http.begin(client, fullUrl);

    // Send an empty HTTP POST request to Django
    int httpResponseCode = http.POST("");

    if (httpResponseCode > 0) {
      Serial.printf("Trigger '%s' sent! Django Response: %d\n", action.c_str(), httpResponseCode);
    } else {
      Serial.printf("Failed to send '%s'. Error: %s\n", action.c_str(), http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("Error: Lost Wi-Fi connection!");
  }
}

void loop() {
  // Check if Start Button (GPIO 4) is pressed
  if (digitalRead(START_BUTTON) == LOW) {
    Serial.println("Physical Start Button Detected!");
    sendTrigger("start");
    delay(400); // Debounce delay to prevent a single press from sending double requests
  }

  // Check if Stop Button (GPIO 5) is pressed
  if (digitalRead(STOP_BUTTON) == LOW) {
    Serial.println("Physical Stop Button Detected!");
    sendTrigger("stop");
    delay(400); // Debounce delay
  }
}
