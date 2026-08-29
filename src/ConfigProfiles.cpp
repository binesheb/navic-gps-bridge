#include "ConfigProfiles.h"

String ConfigProfiles::name(OutputProfile p){switch(p){case OutputProfile::GenericGPS:return "Generic GPS";case OutputProfile::LegacyGPS:return "Legacy GPS";case OutputProfile::Marine:return "Marine";case OutputProfile::Automotive:return "Automotive";case OutputProfile::FlightController:return "Flight Controller";}return "Generic GPS";}

bool ConfigProfiles::apply(const String &profile, BridgeConfig &c){
  String p=profile;p.toLowerCase();
  if(p=="generic"||p=="gps"){c.gpsOutBaud=9600;c.gpsCompatibility=true;return true;}
  if(p=="legacy"){c.gpsOutBaud=4800;c.gpsCompatibility=true;return true;}
  if(p=="marine"){c.gpsOutBaud=4800;c.gpsCompatibility=true;return true;}
  if(p=="automotive"){c.gpsOutBaud=9600;c.gpsCompatibility=true;return true;}
  if(p=="flight"||p=="flightcontroller"){c.gpsOutBaud=115200;c.gpsCompatibility=false;return true;}
  return false;
}
