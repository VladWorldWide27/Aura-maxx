export type LatLng = { lat: number; lng: number }; //latitude longitude pair

export type BuildingEntrance = {
  id: string;
  name: string;
  location: LatLng;
  entranceFloor: number;
};

/* parameter estimate based on the benedum hall inside virtual tour:
floor height: 3.8 m
entrance to elevator: 40m
stairs/elevator landing to classroom: 55m
avg person stair climbing rate: 13s/floor
avg wait time for elevators: 30s (nonbusy), 70s (busy)
elevator s per floors: 2.5s/floor
elevator door wait buffer: 8s
indoor walking speed: 1.1m/s
door/entry/dilly dally: 12s
wayfinding penalty: 8s
*/

//metadata about the building
export type BuildingMeta = {
  id: string;
  name: string;
  floorHeightMeters?: number; //default 3.8 meters
  entrances: BuildingEntrance[]; //at least one
  avgIndoorToCoreMeters?: number; //default 35
  avgCoreToDestMeters?: number; //default 35
};

export type VerticalMode = "stairs" | "elevator" | "auto";

export type IndoorParams = { //from above
  verticalMode?: VerticalMode; //default "stairs"
  stairsSecondsPerFloor?: number; //default physics-based if not set
  elevatorWaitSeconds?: number; //default 30
  elevatorSecPerFloor?: number; //default 2.5
  elevatorDoorSeconds?: number; //default 8
  indoorWalkSpeedMps?: number; //default 1.1
  transitionPenaltySec?: number; //default 12 (entry/security)
  wayfindingPenaltySec?: number; //default 8
};
export type OutdoorParams = {
    //pass mapbox token here to enable the routing
    mapboxToken?: string;
    walkProfile?: "walking" | "walking-traffic";
  };
  
  // input for eta, requires origin, building, targetfloor
  export type EstimateOptions = {
    origin: LatLng; //start point
    building: BuildingMeta; //destination building metadata
    targetFloor: number;
    preferredEntranceId?: string; //pick a specific entrance (optional)
    indoor?: IndoorParams;
    outdoor?: OutdoorParams;
  
    //AVOID network call during dev:
    //if set, skip mapbox and just use provided outdoor seconds
    precomputedOutdoorDurationSec?: number;
  
    // for indoor distances from own floorplan/graph
    indoorToCoreMetersOverride?: number;
    coreToDestMetersOverride?: number;
  };


//helper methods
//computes great-circle distance between two lat/long points using haversine
function haversineMeters(a: LatLng, b: LatLng): number {
    const R = 6371000; //earths radius in m
    const dLat = (Math.PI/180) * (b.lat - a.lat); //convert degree to radian, make haversine term, return distance m
    const dLng = (Math.PI/180) * (b.lng - a.lng);
    const lat1 = (Math.PI/180) * a.lat;
    const lat2 = (Math.PI/180) * b.lat;
    const x = Math.sin(dLat/2)**2 + Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLng/2)**2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  
  //choose closest entrance through haversine distance and return closest one
  function pickEntrance(origin: LatLng, entrances: BuildingEntrance[]): BuildingEntrance {
    let best = entrances[0], bestD = Infinity;
    for (const e of entrances) {
      const d = haversineMeters(origin, e.location);
      if (d < bestD) { best = e; bestD = d; }
    }
    return best;
  }
  
  //ask mapbox for walking route and return duration, throws error for no token
  //defaults to walking, build url with origin/destination as long/lat pairs
  // fetch url, error if bad
  // parse json
  
  async function getOutdoorDurationSec(origin: LatLng, dest: LatLng, p?: OutdoorParams): Promise<number> {
    // if no token provided require the caller to pass precomputedOutdoorDurationSec instead
    if (!p?.mapboxToken) {
      throw new Error("No Mapbox token. Pass precomputedOutdoorDurationSec to avoid network calls.");
    }
    const profile = p.walkProfile ?? "walking";
    const url = `https://api.mapbox.com/directions/v5/mapbox/${profile}/${origin.lng},${origin.lat};${dest.lng},${dest.lat}?alternatives=false&geometries=geojson&overview=false&steps=false&access_token=${p.mapboxToken}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Mapbox Directions error: ${res.status}`);
    const json = await res.json();
    const duration = json?.routes?.[0]?.duration;
    if (typeof duration !== "number") throw new Error("No route found");
    return duration; // seconds
  }

  //two get and one post
  //post: add an obstacle
  //get: gives way