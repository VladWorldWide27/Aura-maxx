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

  //need helpers to: calculate shortest distance between lat long points, calculate shortest distance between
  // great circle distance: shortest possible path between two points on the surface of a sphere

  //ask mapbox for walking route and return duration, throws error for no token
//defaults to walking, build url with origin/destination as long/lat pairs
// fetch url, error if bad
// parse json