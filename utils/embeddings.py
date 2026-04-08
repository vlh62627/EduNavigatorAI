import os
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

import pandas as pd
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
EMBED_MODEL    = os.getenv("EMBED_MODEL",    "all-MiniLM-L6-v2")
COLLECTION     = "schools"

# ── Embedding model — lazy loaded once ────────────
_embed_model = None


def get_embed_model():
    """
    Load embedding model once and reuse.
    Lazy loading prevents issues with Streamlit
    cache context and module imports.
    """
    global _embed_model
    if _embed_model is None:
        print("🔄 Loading embedding model...")
        _embed_model = SentenceTransformer(EMBED_MODEL)
        print("✅ Embedding model loaded.")
    return _embed_model


def get_chroma_client():
    """Return a silent persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path     = CHROMA_DB_PATH,
        settings = Settings(anonymized_telemetry=False)
    )


def build_document(row):
    """
    Convert one CSV row into a rich text document
    for embedding. The richer the text, the better
    the RAG retrieval quality.
    """
    return f"""
School Name: {row['name']}
Type: {row['type']} | Level: {row['level']}
Location: {row['city']}, {row['county']} County, {row['state']}
Rating: {row['rating']}/10
Tuition: ${row['tuition_min']} - ${row['tuition_max']} per year
Students: {row['student_count']} | Teacher-Student Ratio: {row['teacher_student_ratio']}
AP Courses Available: {row['ap_courses']}
Clubs and Organizations: {row['clubs']} clubs
Application Deadline: {row['application_deadline']}
Website: {row['website']}
Description: {row['description']}
""".strip()


def load_vector_db():
    """
    Load ChromaDB. If already populated, skip
    re-embedding to save time on subsequent runs.
    """
    client     = get_chroma_client()
    collection = client.get_or_create_collection(
        name     = COLLECTION,
        metadata = {"hnsw:space": "cosine"}
    )

    if collection.count() > 0:
        print(f"✅ ChromaDB loaded with {collection.count()} schools.")
        return collection

    print("🔄 Building vector database from CSV...")
    df    = pd.read_csv("data/schools.csv")
    model = get_embed_model()

    documents  = []
    embeddings = []
    metadatas  = []
    ids        = []

    for _, row in df.iterrows():
        text      = build_document(row)
        embedding = model.encode(text).tolist()

        documents.append(text)
        embeddings.append(embedding)
        ids.append(str(row["school_id"]))
        metadatas.append({
            "name":        str(row["name"]),
            "type":        str(row["type"]),
            "level":       str(row["level"]),
            "state":       str(row["state"]),
            "county":      str(row["county"]),
            "city":        str(row["city"]),
            "rating":      float(row["rating"]),
            "tuition_min": int(row["tuition_min"]),
            "tuition_max": int(row["tuition_max"]),
            "ap_courses":  int(row["ap_courses"]),
            "clubs":       int(row["clubs"]),
            "website":     str(row["website"]),
            "source":      "csv",
        })

    collection.add(
        documents  = documents,
        embeddings = embeddings,
        metadatas  = metadatas,
        ids        = ids
    )

    print(f"✅ Vector DB built with {collection.count()} schools.")
    return collection


def query_vector_db(collection, query_text, filters=None, n_results=5):
    """
    Semantic search with optional metadata filters.
    filters example: {"state": "Texas", "level": "High School"}
    """
    query_embedding = get_embed_model().encode(query_text).tolist()

    where_clause = {}
    if filters:
        active = {
            k: v for k, v in filters.items()
            if v and v != "All"
        }
        if len(active) == 1:
            key, val     = list(active.items())[0]
            where_clause = {key: val}
        elif len(active) > 1:
            where_clause = {
                "$and": [{k: v} for k, v in active.items()]
            }

    results = collection.query(
        query_embeddings = [query_embedding],
        n_results        = n_results,
        where            = where_clause if where_clause else None,
        include          = ["documents", "metadatas", "distances"]
    )

    return results


def cache_api_schools(collection, schools, source="api"):
    """
    Cache API-fetched schools into ChromaDB so
    repeat queries are instant without API calls.
    """
    if not schools:
        return

    # Get existing IDs to avoid duplicates
    try:
        existing     = collection.get()
        existing_ids = set(existing.get("ids", []))
    except Exception:
        existing_ids = set()

    documents  = []
    embeddings = []
    metadatas  = []
    ids        = []

    model = get_embed_model()

    for school in schools:
        school_id = str(school.get("school_id", ""))
        if not school_id or school_id in existing_ids:
            continue

        # Build rich document for embedding
        doc = f"""
School Name: {school.get('name', '')}
Type: {school.get('type', '')} | Level: {school.get('level', '')}
Location: {school.get('city', '')}, {school.get('state', '')}
Tuition: ${school.get('tuition_min', 0)} - ${school.get('tuition_max', 0)}
Students: {school.get('student_count', 0)}
Description: {school.get('description', '')}
""".strip()

        embedding = model.encode(doc).tolist()

        documents.append(doc)
        embeddings.append(embedding)
        ids.append(school_id)
        metadatas.append({
            "name":        str(school.get("name",        "")),
            "type":        str(school.get("type",        "Public")),
            "level":       str(school.get("level",       "")),
            "state":       str(school.get("state",       "")),
            "county":      str(school.get("county",      "")),
            "city":        str(school.get("city",        "")),
            "rating":      float(school.get("rating",    0.0)),
            "tuition_min": int(school.get("tuition_min", 0)),
            "tuition_max": int(school.get("tuition_max", 0)),
            "ap_courses":  int(school.get("ap_courses",  0)),
            "clubs":       int(school.get("clubs",       0)),
            "website":     str(school.get("website",     "")),
            "source":      str(source),
        })

    if ids:
        try:
            collection.add(
                documents  = documents,
                embeddings = embeddings,
                metadatas  = metadatas,
                ids        = ids
            )
            print(f"   💾 Cached {len(ids)} schools to ChromaDB.")
        except Exception as e:
            print(f"   ⚠️ Cache write error: {e}")


def is_cached(collection, state, level):
    """
    Check if schools for this state + level
    combination are already in ChromaDB.
    Returns True if cache hit, False if miss.
    """
    try:
        results = collection.get(
            where = {
                "$and": [
                    {"state": state},
                    {"level": level}
                ]
            },
            limit = 1
        )
        return len(results.get("ids", [])) > 0
    except Exception:
        return False


def get_cache_stats(collection):
    """
    Return stats about what is currently cached.
    Useful for debugging and UI display.
    """
    try:
        total = collection.count()
        all_meta = collection.get(
            include=["metadatas"]
        )
        metadatas = all_meta.get("metadatas", [])

        states = set()
        levels = set()
        for m in metadatas:
            if m.get("state"):
                states.add(m["state"])
            if m.get("level"):
                levels.add(m["level"])

        return {
            "total":  total,
            "states": len(states),
            "levels": len(levels),
        }
    except Exception:
        return {"total": 0, "states": 0, "levels": 0}