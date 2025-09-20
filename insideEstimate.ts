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

export type IndoorParams = {
  verticalMode?: VerticalMode; //default "stairs"
  stairsSecondsPerFloor?: number; //default physics-based if not set
  elevatorWaitSeconds?: number; //default 30
  elevatorSecPerFloor?: number; //default 2.5
  elevatorDoorSeconds?: number; //default 8
  indoorWalkSpeedMps?: number; //default 1.1
  transitionPenaltySec?: number; //default 12 (entry/security)
  wayfindingPenaltySec?: number; //default 8
};