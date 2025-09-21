from typing import List, Dict, Optional, Tuple
import numpy as np
from scipy.spatial import KDTree
import heapq
import math
from backend.models.database import nodes_collection, edges_collection, obstacles_collection

class NavigationService:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.building_nodes = {}  # Map building names to node IDs
        self.kd_tree = None
        self.node_coords = []
        self.node_ids = []
        
    async def initialize(self):
        """Load graph data from MongoDB"""
        await self._load_nodes()
        await self._load_edges()
        self._build_kdtree()
        
    async def _load_nodes(self):
        """Load all active nodes from MongoDB"""
        cursor = nodes_collection.find({"active": True})
        self.nodes = {}
        self.building_nodes = {}
        self.node_coords = []
        self.node_ids = []
        
        async for node_doc in cursor:
            node_id = node_doc["nodeId"]
            coords = node_doc["coordinates"]
            lat, lng = coords["lat"], coords["lng"]
            name = node_doc["name"]
            node_type = node_doc.get("type", "waypoint")
            
            self.nodes[node_id] = {
                "id": node_id,
                "coords": (lat, lng),
                "name": name,
                "type": node_type,
                "neighbors": []
            }
            
            self.node_coords.append([lat, lng])
            self.node_ids.append(node_id)
            
            # If this is a building entrance, add it to building_nodes
            if node_type == "building" or "entrance" in name.lower():
                # Use the building name as the key (clean it up)
                building_name = name.lower().strip()
                self.building_nodes[building_name] = node_id
                
    async def _load_edges(self):
        """Load all active edges from MongoDB and build adjacency lists"""
        cursor = edges_collection.find({"active": True})
        
        async for edge_doc in cursor:
            from_node = edge_doc["from"]
            to_node = edge_doc["to"]
            
            # Add bidirectional connections
            if from_node in self.nodes:
                self.nodes[from_node]["neighbors"].append(to_node)
            if to_node in self.nodes:
                self.nodes[to_node]["neighbors"].append(from_node)
                
    def _build_kdtree(self):
        """Build KDTree for spatial queries"""
        if self.node_coords:
            self.kd_tree = KDTree(np.array(self.node_coords))
            
    def find_nearest_node(self, lat: float, lng: float) -> Optional[str]:
        """Find the nearest node to given coordinates"""
        if not self.kd_tree:
            return None
            
        dist, idx = self.kd_tree.query([lat, lng])
        return self.node_ids[idx]
        
    def get_building_node(self, building_name: str) -> Optional[str]:
        """Get node ID for a building by name"""
        building_name = building_name.lower().strip()
        return self.building_nodes.get(building_name)
        
    def get_available_buildings(self) -> List[str]:
        """Get list of all available building names"""
        return list(self.building_nodes.keys())
        
    def haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two GPS coordinates in meters"""
        lat1, lng1 = coord1
        lat2, lng2 = coord2
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # Earth's radius in meters
        
        return c * r
        
    async def get_blocked_nodes(self) -> set:
        """Get set of node IDs that are blocked by obstacles"""
        blocked_nodes = set()
        cursor = obstacles_collection.find({"active": True, "ai_verified": True})
        
        async for obstacle in cursor:
            coords = obstacle["coords"]
            lat, lng = coords["lat"], coords["lng"]
            
            # Find nearest node to obstacle
            nearest_node = self.find_nearest_node(lat, lng)
            if nearest_node:
                # Check if obstacle is close enough to block the node (within 10 meters)
                node_coords = self.nodes[nearest_node]["coords"]
                distance = self.haversine_distance((lat, lng), node_coords)
                if distance <= 10:  # 10 meter threshold
                    blocked_nodes.add(nearest_node)
                    
        return blocked_nodes
        
    async def find_path(self, start_building: str, end_building: str) -> Optional[Dict]:
        """Find path between two buildings using Dijkstra's algorithm"""
        # Get node IDs for buildings
        start_node_id = self.get_building_node(start_building)
        end_node_id = self.get_building_node(end_building)
        
        if not start_node_id or not end_node_id:
            return None
            
        # Get blocked nodes from obstacles
        blocked_nodes = await self.get_blocked_nodes()
        
        # Dijkstra's algorithm
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[start_node_id] = 0
        previous = {}
        visited = set()
        
        # Priority queue: (distance, node_id)
        pq = [(0, start_node_id)]
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited or current_node in blocked_nodes:
                continue
                
            visited.add(current_node)
            
            if current_node == end_node_id:
                # Reconstruct path
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = previous.get(current_node)
                path.reverse()
                
                # Convert to coordinates for frontend
                coordinates = []
                for node_id in path:
                    lat, lng = self.nodes[node_id]["coords"]
                    coordinates.append([lng, lat])  # GeoJSON format [lng, lat]
                    
                return {
                    "path_nodes": path,
                    "coordinates": coordinates,
                    "start_building": start_building,
                    "end_building": end_building,
                    "blocked_nodes": list(blocked_nodes)
                }
                
            # Check neighbors
            for neighbor_id in self.nodes[current_node]["neighbors"]:
                if neighbor_id in visited or neighbor_id in blocked_nodes:
                    continue
                    
                if neighbor_id not in self.nodes:
                    continue
                    
                # Calculate distance to neighbor
                current_coords = self.nodes[current_node]["coords"]
                neighbor_coords = self.nodes[neighbor_id]["coords"]
                edge_weight = self.haversine_distance(current_coords, neighbor_coords)
                
                new_distance = distances[current_node] + edge_weight
                
                if new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    previous[neighbor_id] = current_node
                    heapq.heappush(pq, (new_distance, neighbor_id))
                    
        return None  # No path found

# Global navigation service instance
navigation_service = NavigationService()
