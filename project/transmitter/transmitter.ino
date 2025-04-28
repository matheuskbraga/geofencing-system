#include <ESP8266WiFi.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>

// Config Wi-Fi
const char* ssid = "NOTDOMATHEUS";        // Nome do seu Hotspot
const char* password = "87654321";       // Senha do seu Hotspot

const char* host = "192.168.137.1";      // IP do PC (Hotspot Windows)
const uint16_t port = 3333;              // Porta do servidor Python

WiFiClient client;

// GPS Config
#define RX 14
#define TX 12
#define GPS_BAUD 9600

TinyGPSPlus gps;
SoftwareSerial gpsSerial(RX, TX);

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPS_BAUD);

  // Conectar no Wi-Fi
  WiFi.begin(ssid, password);
  Serial.println("Conectando ao Hotspot...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado ao Wi-Fi!");
  Serial.print("IP local: ");
  Serial.println(WiFi.localIP());

  // Conectar ao servidor TCP
  if (client.connect(host, port)) {
    Serial.println("Conectado ao servidor TCP!");
  } else {
    Serial.println("Falha ao conectar no servidor TCP!");
  }
}

void loop() {
  if (!client.connected()) {
    Serial.println("Desconectado do servidor. Tentando reconectar...");
    client.stop();
    if (client.connect(host, port)) {
      Serial.println("Reconectado ao servidor TCP!");
    } else {
      delay(1000);
      return;
    }
  }

  // Atualiza informações do GPS
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // Se tiver novas informações
  if (gps.location.isUpdated()) {
    String message = "";
    message += "LAT:" + String(gps.location.lat(), 6) + ",";
    message += "LON:" + String(gps.location.lng(), 6) + ",";
    message += "ALT:" + String(gps.altitude.meters(), 2);

    Serial.println("Enviando: " + message);
    client.println(message); // Envia para o servidor

    delay(1000); // Espera 1 segundo para nova leitura/envio
  }
}
