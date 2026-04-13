import logging
import uuid
from datetime import datetime, timezone
from app.config import settings
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from app.services.llm_service import generate_embeddings

logger = logging.getLogger(__name__)

if settings.qdrant_url and settings.qdrant_api_key:
    qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
else:
    qdrant = AsyncQdrantClient(location=":memory:")

COLLECTION_NAME = "legal_memory"
VECTOR_SIZE = 1536

async def init_qdrant():
    try:
        exists = await qdrant.collection_exists(COLLECTION_NAME)
        if not exists:
            logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
            await qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            # Create payload index on user_id for high-performance filtering
            await qdrant.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="user_id",
                field_schema="keyword"
            )
    except Exception as e:
        logger.error(f"Error initializing Qdrant: {e}")

async def store_memory(user_id: str, text: str, issue_type: str = "general"):
    """
    1. Generates embedding internally
    2. Stores new semantic memory interaction into Qdrant for a user
    """
    try:
        embedding = await generate_embeddings(text)
        point_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).isoformat()
        
        await qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "user_id": user_id,
                        "text": text,
                        "timestamp": timestamp,
                        "issue_type": issue_type
                    }
                )
            ]
        )
        logger.info(f"Memory {point_id} stored for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")

async def retrieve_context(user_id: str, query: str, top_k: int = 3) -> str:
    """
    1. Embeds the user query
    2. Searches top-k similar interactions exclusively assigned to this user_id
    """
    try:
        query_embedding = await generate_embeddings(query)
        
        results = await qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )
        
        if not results:
            return ""
            
        context_parts = []
        for res in results:
            timestamp = res.payload.get('timestamp', 'unknown_time')
            text = res.payload.get('text', '')
            context_parts.append(f"[{timestamp}] Past interaction: {text}")
            
        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Failed to retrieve context: {e}")
        return ""


async def get_recent_memories(user_id: str, limit: int = 20):
    """
    Returns recent stored memories for the given user_id.
    """
    try:
        records = []
        offset = None

        while len(records) < limit:
            batch, next_offset = await qdrant.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=min(50, limit - len(records)),
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            records.extend(batch)

            if next_offset is None:
                break

            offset = next_offset

        items = []
        for record in records:
            payload = record.payload or {}
            items.append({
                "id": str(record.id),
                "issue_summary": payload.get("text", "Untitled issue"),
                "date_time": payload.get("timestamp", ""),
                "issue_type": payload.get("issue_type", "general"),
            })

        items.sort(key=lambda item: item["date_time"], reverse=True)
        return items[:limit]
    except Exception as e:
        logger.error(f"Failed to fetch recent memories: {e}")
        return []
