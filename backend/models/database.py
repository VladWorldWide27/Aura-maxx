from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://<your_username>:<your_password>@hackathon-cluster.wt77kap.mongodb.net/?retryWrites=true&w=majority&appName=hackathon-cluster"
DB_NAME = "hackathon"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

obstacles_collection = db["obstacles"]
nodes_collection = db["graph_nodes"]
edges_collection = db["graph_edges"]
