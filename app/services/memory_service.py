import logging
import hashlib
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
DEMO_POINTS = [
    {
        "id": "demo-memory-1",
        "user_id": "demo_user",
        "text": "Issue: Unlawful eviction | Facts: Landlord changed the locks without notice and removed personal property | Action: Send a legal notice and document all losses.",
        "issue_type": "legal_complaint",
    },
    {
        "id": "demo-memory-2",
        "user_id": "demo_user",
        "text": "Issue: Workplace wage dispute | Facts: Employer delayed salary payments and did not provide a written explanation | Action: Collect payslips and file a formal complaint.",
        "issue_type": "legal_complaint",
    },
]

def _local_demo_embedding(text: str) -> list[float]:
    """
    Deterministic local embedding used only for demo seeding.
    Keeps startup independent from OpenAI connectivity or API keys.
    """
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    while len(values) < VECTOR_SIZE:
        for byte in seed:
            values.append((byte / 255.0) * 2.0 - 1.0)
            if len(values) == VECTOR_SIZE:
                break
        seed = hashlib.sha256(seed).digest()
    return values

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

async def seed_demo_memories():
    """
    Seeds exactly two deterministic demo records in Qdrant.
    Uses fixed point IDs so repeated startups overwrite the same demo data
    instead of creating duplicates.
    """
    if not settings.qdrant_seed_demo_data:
        logger.info("Qdrant demo seeding is disabled.")
        return

    try:
        exists = await qdrant.collection_exists(COLLECTION_NAME)
    except Exception as e:
        logger.warning(f"Qdrant is unreachable, skipping demo seed: {e}")
        return

    try:
        if not exists:
            await init_qdrant()
    except Exception as e:
        logger.error(f"Failed to prepare demo collection: {e}")
        return

    if not exists:
        logger.info(f"Created Qdrant collection for demo data: {COLLECTION_NAME}")

    points = []
    for item in DEMO_POINTS:
        embedding = _local_demo_embedding(item["text"])
        points.append(
            PointStruct(
                id=item["id"],
                vector=embedding,
                payload={
                    "user_id": item["user_id"],
                    "text": item["text"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "issue_type": item["issue_type"],
                    "seed_type": "demo",
                },
            )
        )

    try:
        await qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info("Seeded 2 demo memories in Qdrant.")
    except Exception as e:
        logger.error(f"Failed to seed demo memories: {e}")

async def store_memory(user_id: str, text: str, issue_type: str = "general"):
    """
    1. Generates embedding internally
    2. Stores new semantic memory interaction into Qdrant for a user
    """
    if not settings.qdrant_allow_runtime_writes:
        logger.info("Runtime Qdrant writes are disabled; skipping store_memory.")
        return

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
