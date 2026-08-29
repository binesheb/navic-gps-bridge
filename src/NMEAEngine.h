#pragma once
#include <Arduino.h>
struct GnssData{bool valid=false,fix=false;int fixQuality=0,satellites=0;double latitude=0,longitude=0,altitude=0,speedKmh=0,course=0,hdop=0;String utcTime,utcDate,lastSentence;};
struct SatelliteData{String constellation;int prn=0,snr=0,elevation=0,azimuth=0;};
class NMEAEngine{public:bool process(const String&);const GnssData&data()const{return state;}const SatelliteData*satellites()const{return sats;}int satelliteCount()const{return satCount;}bool checksumValid(const String&)const;String gpsCompatible(const String&)const;private:GnssData state;SatelliteData sats[32];int satCount=0;double parseCoordinate(const String&,const String&)const;void parseGsv(const String&,const String&);};