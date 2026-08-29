#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

static const int GNSS_RX = 16;
static const int GNSS_TX = 17;
static const uint32_t GNSS_BAUD = 9600;
static const uint16_t TCP_PORT = 10110;

HardwareSerial GNSS(1);
WiFiServer nmeaServer(TCP_PORT);
WebServer web(80);

String lastNmea;
unsigned long sentenceCount = 0;

String gpsCompatible(const String &line) {
  if (line.length() < 6 || line[0] != '$') return line;
  String out = line;
  if (out.startsWith("$GN")) {
    out.setCharAt(1, 'G');
    out.setCharAt(2, 'P');
  }
  return out;
}

void handleStatus() {
  JsonDocument doc;
  doc["status"] = "running";
  doc["sentences"] = sentenceCount;
  doc["last_nmea"] = lastNmea;
  doc["ip"] = WiFi.localIP().toString();
  String body;
  serializeJson(doc, body);
  web.send(200, "application/json", body);
}

void setup() {
  Serial.begin(115200);
  GNSS.begin(GNSS_BAUD, SERIAL_8N1, GNSS_RX, GNSS_TX);

  WiFi.mode(WIFI_AP);
  WiFi.softAP("NavIC-GPS-Bridge", "navicgps");
  nmeaServer.begin();

  web.on("/api/status", HTTP_GET, handleStatus);
  web.begin();

  Serial.println("NavIC GPS Bridge started");
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  web.handleClient();

  while (GNSS.available()) {
    String line = GNSS.readStringUntil('\n');
    line.trim();
    if (!line.length()) continue;

    lastNmea = line;
    sentenceCount++;

    String output = gpsCompatible(line);
    Serial.println(output);

    WiFiClient client = nmeaServer.available();
    if (client) {
      client.println(output);
    }
  }
}
