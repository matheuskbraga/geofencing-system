#include <ESP8266WiFi.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <WiFiUdp.h>

// Definir os pinos RX e TX para SoftwareSerial
#define RX 14
#define TX 12

#define GPS_BAUD 9600

// Defina as credenciais do Access Point
const char* ssid = "nome_do_ap";  // Nome do Access Point
const char* password = "senha_ap";  // Senha do Access Point

// Endereço IP do PC e a porta UDP
const char* serverIP = "192.168.4.1";  // Endereço IP do PC
const int serverPort = 8888;           // Porta UDP

// Inicializar o objeto Wi-Fi e o UDP
WiFiUDP udp;
TinyGPSPlus gps;
SoftwareSerial gpsSerial(RX, TX);

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(GPS_BAUD);

  // Conectar à rede Wi-Fi
  Serial.println();
  Serial.print("Conectando ao WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println("Conectado ao WiFi!");
  Serial.print("IP do ESP8266: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Verificar dados do GPS
  delay(20000);
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  if (gps.location.isUpdated()) {
    // Coletar os dados de GPS
    double latitude = gps.location.lat();
    double longitude = gps.location.lng();
    double speed = gps.speed.kmph();
    double altitude = gps.altitude.meters();
    int satellites = gps.satellites.value();

    // Preparar a mensagem para enviar
    String data = "LAT: " + String(latitude, 6) + ", LONG: " + String(longitude, 6) +
                  ", SPEED: " + String(speed) + " km/h, ALT: " + String(altitude) + " m, Satellites: " + String(satellites);
    
    // Enviar os dados via UDP para o PC
    udp.beginPacket(serverIP, serverPort);
    udp.write(data.c_str());
    udp.endPacket();
    
    // Imprimir no Serial Monitor
    Serial.println(data);
  }

  delay(2000); // Enviar dados a cada 1 segundo
}
