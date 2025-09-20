import numpy as np
from scipy.spatial import KDTree
import heapq
import time

class Node:
    def __init__(self, node_id, gps_coords, name):
        self.id = node_id
        self.gps_coords = gps_coords  # (lat, lon)
        self.name = name
        self.links = []  # List of node ids

class Graph:
    def __init__(self, sgraph):
        self.nodes = {}
        self.node_coords = []
        self.node_ids = []
        # Build nodes from sgraph
        for node_data in sgraph:
            node = Node(node_data['id'], node_data['gps_coords'], node_data['name'])
            node.links = node_data.get('links', [])
            self.nodes[node.id] = node
            self.node_coords.append(node.gps_coords)
            self.node_ids.append(node.id)
        self.kd_tree = KDTree(np.array(self.node_coords))

    def find_nearest(self, gps_coords):
        dist, idx = self.kd_tree.query(gps_coords)
        node_id = self.node_ids[idx]
        return self.nodes[node_id]

    def neighbors(self, node_id):
        return [self.nodes[nid] for nid in self.nodes[node_id].links if nid in self.nodes]

    def distance(self, node1, node2):
        # Haversine or Euclidean; here Euclidean for simplicity
        return np.linalg.norm(np.array(node1.gps_coords) - np.array(node2.gps_coords))

    def shortest_path(self, start_coords, end_coords, unavailable_ids=None):
        start_node = self.find_nearest(start_coords)
        end_node = self.find_nearest(end_coords)
        unavailable_ids = unavailable_ids or set()
        # Dijkstra's algorithm
        queue = [(0, start_node.id, [])]
        visited = set()
        while queue:
            cost, current_id, path = heapq.heappop(queue)
            if current_id in visited or current_id in unavailable_ids:
                continue
            visited.add(current_id)
            path = path + [current_id]
            if current_id == end_node.id:
                return path
            for neighbor in self.neighbors(current_id):
                if neighbor.id not in visited and neighbor.id not in unavailable_ids:
                    heapq.heappush(queue, (
                        cost + self.distance(self.nodes[current_id], neighbor),
                        neighbor.id,
                        path
                    ))
        return None

    def ids_to_coords(self, path_ids):
        return [list(self.nodes[nid].gps_coords)[::-1] for nid in path_ids if nid in self.nodes]

class Navigator:
    def __init__(self, storage):
        self.storage = storage
        self.obstacles = []         # List of dicts: {'id', 'coords', 'timestamp'}
        self.unavailable_ids = set()
        # Get static graph
        # sgraph = self.storage.get_statqic_graph()
        sgraph = [
            {'id': 0, 'gps_coords': (40.442520, -79.957635), 'name': 'P0', 'links': [1]},
            {'id': 1, 'gps_coords': (40.442574, -79.957729), 'name': 'P1', 'links': [0, 2]},
            {'id': 2, 'gps_coords': (40.442628, -79.957824), 'name': 'P2', 'links': [1, 3]},
            {'id': 3, 'gps_coords': (40.442682, -79.957918), 'name': 'P3', 'links': [2]},
        ]

        # Get obstacles
        # obstacles = self.storage.get_obstacles()

        # Construct graph
        # for obstacle in obstacles:
        #     sgraph.add_obstacle(obstacle)
        self.graph = Graph(sgraph)

    def add_obstacle(self, gps_coords):
        """
        Adds an obstacle at the nearest node to gps_coords.
        Marks the node as unavailable for pathfinding.
        """
        node = self.graph.find_nearest(gps_coords)
        self.unavailable_ids.add(node.id)
        self.obstacles.append({
            'id': node.id,
            'coords': node.gps_coords,
            'timestamp': time.time()
        })

    def navigate(self, start_coords, destination_coords):
        path = self.graph.shortest_path(start_coords, destination_coords, unavailable_ids=self.unavailable_ids)
        if path:
            return self.graph.ids_to_coords(path)
        else:
            self.state = "No path found."
            return None
    
    def graph_from_file(self, filepath):
        """
        Constructs a Graph object from a file with POINT and EDGE lines.
        """
        nodes = {}
        links = {}
        with open(filepath, "r") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == "POINT":
                    pid = int(parts[1])
                    lat = float(parts[2])
                    lon = float(parts[3])
                    name = parts[4] if len(parts) > 4 else f"P{pid}"
                    nodes[pid] = {
                        'id': pid,
                        'gps_coords': (lat, lon),
                        'name': name,
                        'links': []
                    }
                elif parts[0] == "EDGE":
                    src = int(parts[1])
                    dst = int(parts[2])
                    # Add links in both directions for undirected graph
                    links.setdefault(src, []).append(dst)
                    links.setdefault(dst, []).append(src)
        # Attach links to nodes
        for pid, node in nodes.items():
            node['links'] = links.get(pid, [])
        # Build and return the Graph
        return Graph(list(nodes.values()))

        

nav = Navigator(None)
# construct graph from file
nav.graph = nav.graph_from_file("graph_points.txt")

start_point = (40.443175, -79.956718) # Thackeray left and Fifth left
dest_point = (40.445045, -79.957418) # OHara left and University Place left


# add obstacle on Thackeray left sidewalk
nav.add_obstacle((40.443889, -79.957565))
# add obstacle on Thackeray right sidewalk
nav.add_obstacle((40.443618, -79.957034))

print(nav.unavailable_ids)
# It has to offer route via University Place left sidewalk
print(nav.navigate(start_point, dest_point))

# Now you can use graph.shortest_path(...) etc.
