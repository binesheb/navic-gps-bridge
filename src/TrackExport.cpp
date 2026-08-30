#include "TrackExport.h"

String trackToCsv(const GnssLogger &logger) {
  String out = "latitude,longitude,altitude_m,speed_kmh,timestamp_ms\n";
  for (size_t i = 0; i < logger.size(); ++i) {
    const auto &p = logger.at(i);
    out += String(p.lat, 7) + "," + String(p.lon, 7) + "," + String(p.altitude, 2) + "," + String(p.speedKmh, 2) + "," + String(p.timestamp) + "\n";
  }
  return out;
}

String trackToGpx(const GnssLogger &logger, const String &name) {
  String out = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  out += "<gpx version=\"1.1\" creator=\"NavIC-GPS-Bridge\" xmlns=\"http://www.topografix.com/GPX/1/1\">\n";
  out += "<trk><name>" + name + "</name><trkseg>\n";
  for (size_t i = 0; i < logger.size(); ++i) {
    const auto &p = logger.at(i);
    out += "<trkpt lat=\"" + String(p.lat, 7) + "\" lon=\"" + String(p.lon, 7) + "\"><ele>" + String(p.altitude, 2) + "</ele></trkpt>\n";
  }
  out += "</trkseg></trk></gpx>\n";
  return out;
}

String trackToKml(const GnssLogger &logger, const String &name) {
  String out = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<kml xmlns=\"http://www.opengis.net/kml/2.2\"><Document><name>" + name + "</name><Placemark><LineString><tessellate>1</tessellate><coordinates>\n";
  for (size_t i = 0; i < logger.size(); ++i) {
    const auto &p = logger.at(i);
    out += String(p.lon, 7) + "," + String(p.lat, 7) + "," + String(p.altitude, 2) + " ";
  }
  out += "\n</coordinates></LineString></Placemark></Document></kml>\n";
  return out;
}
