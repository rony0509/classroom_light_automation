#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* mqtt_server = "192.168.1.100";

WiFiClient espClient;
PubSubClient client(espClient);

#define RELAY 2

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;

  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.println("Message: " + msg);

  if (msg == "ON") {
    digitalWrite(RELAY, HIGH);
  } else if (msg == "OFF") {
    digitalWrite(RELAY, LOW);
  }
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Client")) {
      client.subscribe("classroom/light");
    } else {
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY, OUTPUT);
  digitalWrite(RELAY, LOW);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}