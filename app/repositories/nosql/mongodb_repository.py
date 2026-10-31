import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from pymongo import DESCENDING, MongoClient

load_dotenv()


class MongoDBRepository:
    """Acesso às preferências e ao histórico de atividade no MongoDB."""

    def __init__(
        self,
        uri: str | None = None,
        database_name: str | None = None,
    ) -> None:
        self._client = MongoClient(
            uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        )
        name = database_name or os.getenv("MONGODB_DATABASE", "smart_tourism")
        database = self._client[name]
        self._profiles = database["user_profiles"]
        self._interactions = database["user_interactions"]

    def ensure_indexes(self) -> None:
        """Cria índices idempotentes necessários às consultas da aplicação."""
        self._profiles.create_index("user_id", unique=True)
        self._interactions.create_index("event_id", unique=True)
        self._interactions.create_index(
            [("user_id", 1), ("timestamp", DESCENDING)]
        )

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        return self._profiles.find_one({"user_id": user_id}, {"_id": 0})

    def save_profile(
        self,
        user_id: int,
        interests: list[str],
        travel_style: str,
        budget_level: str,
        preferred_activities: list[str],
    ) -> None:
        self._profiles.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "interests": interests,
                    "travel_style": travel_style,
                    "budget_level": budget_level,
                    "preferred_activities": preferred_activities,
                }
            },
            upsert=True,
        )

    def record_interaction(
        self,
        user_id: int,
        event_type: str,
        context: dict[str, Any],
    ) -> str:
        event_id = str(uuid4())
        self._interactions.insert_one(
            {
                "event_id": event_id,
                "user_id": user_id,
                "event_type": event_type,
                "context": context,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        return event_id

    def get_recent_interactions(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit tem de ser pelo menos 1.")

        interactions = (
            self._interactions.find({"user_id": user_id}, {"_id": 0})
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        return list(interactions)

    def close(self) -> None:
        self._client.close()
