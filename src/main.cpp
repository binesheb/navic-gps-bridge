#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include "NMEAEngine.h"

static const int GNSS_RX = 16;
static const int GNSS_TX = 17;
static const int GPS_OUT_TX = 18;
static const uint32_t GNSS_BAUD = 9600;
static const uint32_t GPS_OUT_BAUD = 9600;
static const uint16_t TCP_PORT = 10110;

HardwareSerial GNSS(1);
HardwareSerial GPSOut(2);
WiFiServer nmeaServer(TCP_PORT);
WebServer web(80);
NMEAEngine nmea;

unsigned long sentenceCount = 0;
unsigned long invalidCount = 0;

String page() {
  return R"HTML(<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>NavIC GPS Bridge</title><style>
  body{margin:0;background:#0b1020;color:#e8eefc;font:15px system-ui,sans-serif}header{padding:18px 22px;background:#111a33;display:flex;justify-content:space-between;align-items:center}.live{color:#54e38e}.wrap{max-width:1100px;margin:auto;padding:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.card{background:#141f3d;border:1px solid #26365f;border-radius:16px;padding:18px}.label{color:#91a4d4;font-size:12px;text-transform:uppercase}.value{font-size:26px;font-weight:700;margin-top:7px}.coords{font-size:18px;word-break:break-all}.ok{color:#54e38e}.bad{color:#ff7185}pre{white-space:pre-wrap;max-height:260px;overflow:auto;background:#090e1c;padding:14px;border-radius:12px}@media(max-width:600px){header{padding:14px}.wrap{padding:12px}.value{font-size:22px}}</style></head><body><header><b>🛰 NavIC GPS Bridge</b><span id="status" class="live">● LIVE</span></header><main class="wrap"><div class="grid"><section class="card"><div class="label">Fix</div><div id="fix" class="value">Waiting…</div></section><section class="card"><div class="label">Satellites</div><div id="sat" class="value">—</div></section><section class="card"><div class="label">Speed</div><div id="speed" class="value">—</div></section><section class="card"><div class="label">HDOP</div><div id="hdop" class="value">—</div></section><section class="card"><div class="label">Coordinates</div><div id="coords" class="value coords">—</div></section><section class="card"><div class="label">Altitude / Course</div><div id="nav" class="value">—</div></section></div><section class="card" style="margin-top:14px"><div class="label">Latest NMEA</div><pre id="nmea">Waiting for receiver data…</pre></section></main><script>async function u(){try{let r=await fetch('/api/live'),d=await r.json();fix.textContent=d.fix?'3D / VALID FIX':'NO FIX';fix.className='value '+(d.fix?'ok':'bad');sat.textContent=d.satellites??'—';speed.textContent=(d.speed_kmh||0).toFixed(1)+' km/h';hdop.textContent=d.hdop||'—';coords.textContent=d.latitude.toFixed(6)+', '+d.longitude.toFixed(6);nav.textContent=(d.altitude||0).toFixed(1)+' m / '+(d.course||0).toFixed(0)+'°';nmea.textContent=d.last_nmea||'Waiting…';status.textContent='● LIVE '+d.sentences+' packets'}catch(e){status.textContent='● DISCONNECTED';status.className='bad'}}setInterval(u,500);u();</script></body></html>)HTML";
}

void handleLive() {
  const GnssData &d = nmea.data();
  JsonDocument doc;
  doc["fix"] = d.fix;
  doc["valid"] = d.valid;
  doc["fix_quality"] = d.fixQuality;
  doc["latitude"] = d.latitude;
  doc["longitude"] = d.longitude;
  doc["altitude"] = d.altitude;
  doc["speed_kmh"] = d.speedKmh;
  doc["course"] = d.course;
  doc["satellites"] = d.satellites;
  doc["hdop"] = d.hdop;
  doc["utc_time"] = d.utcTime;
  doc["utc_date"] = d.utcDate;
  doc["last_nmea"] = d.lastSentence;
  doc["sentences"] = sentenceCount;
  doc["invalid"] = invalidCount;
  String body; serializeJson(doc, body);
  web.send(200, "application/json", body);
}

void setup() {
  Serial.begin(115200);
  GNSS.begin(GNSS_BAUD, SERIAL_8N1, GNSS_RX, GNSS_TX);
  GPSOut.begin(GPS_OUT_BAUD, SERIAL_8N1, -1, GPS_OUT_TX);
  WiFi.mode(WIFI_AP);
  WiFi.softAP("NavIC-GPS-Bridge", "navicgps");
  nmeaServer.begin();
  web.on("/", HTTP_GET, [](){ web.send(200, "text/html", page()); });
  web.on("/api/live", HTTP_GET, handleLive);
  web.begin();
  Serial.println("NavIC GPS Bridge ready");
}

void loop() {
  web.handleClient();
  while (GNSS.available()) {
    String line = GNSS.readStringUntil('\n'); line.trim();
    if (!line.length()) continue;
    if (!nmea.process(line)) { invalidCount++; continue; }
    sentenceCount++;
    String output = nmea.gpsCompatible(line);
    GPSOut.println(output);
    Serial.println(output);
    WiFiClient client = nmeaServer.available();
    if (client) client.println(output);
  }
}
