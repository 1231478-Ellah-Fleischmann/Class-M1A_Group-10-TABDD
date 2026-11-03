from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(
    os.getenv("MONGODB_URI"),
    serverSelectionTimeoutMS=10000
)

try:
    client.admin.command("ping")
    print("Ligação ao MongoDB Atlas estabelecida!")
except Exception as e:
    print("Erro na ligação:", e)
finally:
    client.close()