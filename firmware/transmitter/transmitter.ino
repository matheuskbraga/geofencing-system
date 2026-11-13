/*
 * transmitter.ino - Lê o GPS e envia a posição por UDP para o software no PC.
 *
 * Hardware (conforme a imagem do README):
 *   NodeMCU ESP8266  <->  GY-GPS6MV2 (u-blox NEO-6M)
 *   D5 (GPIO14)  <-  TX do GPS
 *   D6 (GPIO12)  ->  RX do GPS
 *   3V3          ->  VCC
 *   GND          ->  GND
 *
 * Bibliotecas (Gerenciador de Bibliotecas da Arduino IDE):
 *   - TinyGPSPlus (Mikal Hart)
 *   Placa: "NodeMCU 1.0 (ESP-12E Module)" (pacote esp8266 da Arduino IDE)
 *
 * Formato do pacote (texto, 1 linha por envio):
 *   lat,lon,alt,sats,hdop,fix\n
 *   ex.: -23.550520,-46.633308,760.2,8,1.10,1
 *   fix = 1 se há posição válida, 0 caso contrário (lat/lon/alt vão zerados).
 */
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <SoftwareSerial.h>
#include <TinyGPSPlus.h>

// ---------- CONFIGURE AQUI ----------
const char* WIFI_SSID = "SEU_WIFI_OU_HOTSPOT";
const char* WIFI_PASS = "SUA_SENHA";

// IP do computador que roda o software. Deixe vazio ("") para enviar em
// broadcast na rede (não precisa saber o IP do PC).
const char* PC_IP = "";
const uint16_t PC_PORT = 5005;          // igual a GPS_UDP_PORT em config.py
// ------------------------------------

const uint8_t  GPS_RX_PIN = 14;         // D5: recebe o TX do GPS
const uint8_t  GPS_TX_PIN = 12;         // D6: envia para o RX do GPS
const uint32_t GPS_BAUD = 9600;         // padrão do NEO-6M
const uint32_t SEND_INTERVAL_MS = 1000; // o NEO-6M atualiza a 1 Hz

SoftwareSerial gpsSerial(GPS_RX_PIN, GPS_TX_PIN);
TinyGPSPlus gps;
WiFiUDP udp;
uint32_t lastSend = 0;

IPAddress targetIp() {
  IPAddress ip;
  if (strlen(PC_IP) > 0 && ip.fromString(PC_IP)) return ip;
  // broadcast = IP local com os bits da máscara invertidos
  return IPAddress((uint32_t)WiFi.localIP() | ~(uint32_t)WiFi.subnetMask());
}

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPS_BAUD);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nConectado. IP local: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // 1) Alimenta o parser com tudo que o GPS enviou (não pode ficar sem ler)
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // 2) A cada intervalo, envia um pacote
  if (millis() - lastSend < SEND_INTERVAL_MS) return;
  lastSend = millis();
  if (WiFi.status() != WL_CONNECTED) return;   // reconecta sozinho (AutoReconnect)

  bool fix = gps.location.isValid() && gps.location.age() < 2000;
  char buf[96];
  snprintf(buf, sizeof(buf), "%.6f,%.6f,%.1f,%u,%.2f,%d\n",
           fix ? gps.location.lat() : 0.0,
           fix ? gps.location.lng() : 0.0,
           fix && gps.altitude.isValid() ? gps.altitude.meters() : 0.0,
           gps.satellites.isValid() ? (unsigned)gps.satellites.value() : 0u,
           gps.hdop.isValid() ? gps.hdop.hdop() : 99.99,
           fix ? 1 : 0);

  udp.beginPacket(targetIp(), PC_PORT);
  udp.write((const uint8_t*)buf, strlen(buf));
  udp.endPacket();
  Serial.print(buf);                           // espelha no monitor serial para depurar

  if (millis() > 10000 && gps.charsProcessed() < 10) {
    Serial.println("Sem dados do GPS: confira a fiação (TX->D5, RX->D6) e o baud.");
  }
}
