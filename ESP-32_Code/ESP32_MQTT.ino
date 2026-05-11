#include <WiFi.h>
#include <PubSubClient.h>

// 🔐 WiFi credentials
const char* ssid = "sahil";
const char* password = "sahil123";
// 🌐 MQTT Broker
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

// 📡 Objects
WiFiClient espClient;
PubSubClient client(espClient);

// 🔌 Relay Pin
int relayPin = 5;

// 📶 WiFi Connect
void setup_wifi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected ✅");
}

// 📩 MQTT Callback
void callback(char* topic, byte* message, unsigned int length) {
  String msg;

  for (int i = 0; i < length; i++) {
    msg += (char)message[i];
  }

  // 🔥 Serial Monitor Debug
  Serial.print("Topic: ");
  Serial.println(topic);

  Serial.print("Message: ");
  Serial.println(msg);

  int humanCount = msg.toInt();

  Serial.print("Human Count: ");
  Serial.println(humanCount);

  // ⚡ Relay Logic
  if (humanCount > 0) {
    digitalWrite(relayPin, LOW);
    Serial.println("Relay ON 💡");
  } else {
    digitalWrite(relayPin, HIGH);
    Serial.println("Relay OFF ❌");
  }

  Serial.println("----------------------");
}

// 🔄 Reconnect MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    // 🔥 Unique Client ID
    String clientId = "ESP32-" + String(random(1000, 9999));

    if (client.connect(clientId.c_str())) {
      Serial.println("Connected ✅");

      client.subscribe("classroom/human_count");
      Serial.println("Subscribed to classroom/human_count");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 sec");

      delay(5000);
    }
  }
}

// ⚙️ Setup
void setup() {
  pinMode(relayPin, OUTPUT);

  Serial.begin(115200);  // 🔥 IMPORTANT

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// 🔁 Loop
void loop() {
  if (!client.connected()) {
    reconnect();
  }

  client.loop();
} 