#include "GeofenceEngine.h"
#include <math.h>

static constexpr double EARTH_RADIUS_M = 6371000.0;
static constexpr double DEG_TO_RAD = 0.017453292519943295;

double GeofenceEngine::distance(double lat1,double lon1,double lat2,double lon2) const {
  double dLat=(lat2-lat1)*DEG_TO_RAD,dLon=(lon2-lon1)*DEG_TO_RAD;
  double a=sin(dLat/2)*sin(dLat/2)+cos(lat1*DEG_TO_RAD)*cos(lat2*DEG_TO_RAD)*sin(dLon/2)*sin(dLon/2);
  return EARTH_RADIUS_M*2*atan2(sqrt(a),sqrt(1-a));
}

bool GeofenceEngine::update(double latitude,double longitude,bool fix,unsigned long now) {
  if(!fence.enabled||!fix) return false;
  bool next=distance(latitude,longitude,fence.latitude,fence.longitude)<=fence.radiusMeters;
  if(!initialized){initialized=true;insideFence=next;return false;}
  if(next==insideFence) return false;
  insideFence=next;events++;
  last=next?"Geofence entered":"Geofence exited";
  return true;
}
