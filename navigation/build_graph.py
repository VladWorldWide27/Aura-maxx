import sys
import os
from coordinate_calc import get_intermediate_points
from pyproj import Geod

RESULT_FILE = "graph_points.txt"  # You can change this path as needed
DIST_THRESHOLD = 3  # meters

def read_existing_points(filepath):
    """Reads all points from the result file. Returns dict: id -> (lat, lon, street_name)"""
    points = {}
    if not os.path.exists(filepath):
        return points
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("POINT"):
                parts = line.strip().split()
                pid = int(parts[1])
                lat = float(parts[2])
                lon = float(parts[3])
                street = parts[4] if len(parts) > 4 else ""
                points[pid] = (lat, lon, street)
    return points

def read_last_point_id(points_dict):
    """Returns the next available point ID (incremental)."""
    if not points_dict:
        return 1
    return max(points_dict.keys()) + 1

def find_close_point(lat, lon, existing_points, geod, threshold=DIST_THRESHOLD):
    """Returns the id of a point within threshold meters, or None."""
    for pid, (plat, plon, _) in existing_points.items():
        _, _, dist = geod.inv(lon, lat, plon, plat)
        if dist < threshold:
            return pid
    return None

def append_points_and_connections(filepath, street_name, points, point_ids, existing_points):
    """Appends new points and their connections to the result file."""
    # Only write new points
    with open(filepath, "a") as f:
        for pid, (lat, lon) in zip(point_ids, points):
            if pid not in existing_points:
                f.write(f"POINT {pid} {lat:.8f} {lon:.8f} {street_name}\n")
        # Write connections (edges)
        for i in range(len(point_ids) - 1):
            f.write(f"EDGE {point_ids[i]} {point_ids[i+1]} {street_name}\n")

def main():
    if len(sys.argv) != 6:
        print("Usage: python build_graph.py <street_name> <start_lat> <start_lon> <end_lat> <end_lon>")
        sys.exit(1)
    street_name = sys.argv[1]
    start_lat = float(sys.argv[2])
    start_lon = float(sys.argv[3])
    end_lat = float(sys.argv[4])
    end_lon = float(sys.argv[5])

    start_point = (start_lat, start_lon)
    end_point = (end_lat, end_lon)

    # Generate intermediate points
    points = get_intermediate_points(start_point, end_point, interval_meters=5)

    # Read existing points
    existing_points = read_existing_points(RESULT_FILE)
    next_id = read_last_point_id(existing_points)
    geod = Geod(ellps='WGS84')

    # Assign IDs, reusing if close enough
    point_ids = []
    for lat, lon in points:
        existing_id = find_close_point(lat, lon, existing_points, geod)
        if existing_id is not None:
            point_ids.append(existing_id)
        else:
            point_ids.append(next_id)
            existing_points[next_id] = (lat, lon, street_name)
            next_id += 1

    # Append new points and edges
    append_points_and_connections(RESULT_FILE, street_name, points, point_ids, read_existing_points(RESULT_FILE))

    print(f"Processed {len(points)} points for '{street_name}'. Connections updated.")

if __name__ == "__main__":
    main()