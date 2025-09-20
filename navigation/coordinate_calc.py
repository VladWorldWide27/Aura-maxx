from pyproj import Geod

def get_intermediate_points(start_point, end_point, interval_meters=10):

    """
    Calculates intermediate GPS points at a specified interval along a geodesic line.

    This function uses the WGS-84 ellipsoid, which is the standard for GPS,
    ensuring high accuracy.

    Args:
        start_point (tuple): A tuple of (latitude, longitude) for the start point.
        end_point (tuple): A tuple of (latitude, longitude) for the end point.
        interval_meters (int): The distance between intermediate points in meters.

    Returns:
        list: A list of (latitude, longitude) tuples, including the start and end points.
    """
    # Use the WGS-84 ellipsoid model, which is the standard for GPS
    geod = Geod(ellps='WGS84')

    # pyproj's functions expect longitude first, then latitude. Let's unpack them correctly.
    start_lon, start_lat = start_point[1], start_point[0]
    end_lon, end_lat = end_point[1], end_point[0]

    # Calculate the total distance and the initial forward direction (azimuth)
    # from the start point to the end point.
    fwd_azimuth, back_azimuth, total_distance = geod.inv(start_lon, start_lat, end_lon, end_lat)

    # Start our list of coordinates with the starting point
    all_points = [start_point]

    # Calculate the number of intermediate points to generate
    # We step along the total distance in increments of our interval
    current_distance = interval_meters
    while current_distance < total_distance:
        # Calculate the next point's coordinates
        # geod.fwd() takes a start lon/lat, azimuth, and distance to find a destination point
        lon, lat, _ = geod.fwd(start_lon, start_lat, fwd_azimuth, current_distance)
        all_points.append((lat, lon))
        current_distance += interval_meters

    # Finally, ensure the exact end point is included in our list
    all_points.append(end_point)

    return all_points

# --- Example Usage ---

# Two points in Pittsburgh, PA (approx. 160 meters apart)
# Point A: Near the Cathedral of Learning
# Point B: Near the Hillman Library
point_a = (40.442520, -79.957635)
point_b = (40.443481, -79.959320)

# Calculate the points every 3 meters between Point A and Point B
intermediate_coordinates = get_intermediate_points(point_a, point_b, interval_meters=10)

# Print the results
print(f"Generated {len(intermediate_coordinates)} points between Point A and Point B.\n")
for i, point in enumerate(intermediate_coordinates):
    print(f"Point {i:>2}: {point[0]:.6f}, {point[1]:.6f}")