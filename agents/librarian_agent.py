import os
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from groq import Groq
from dotenv import load_dotenv
from utils.embeddings import query_vector_db

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
client     = Groq(api_key=os.getenv("GROQ_API_KEY"))


def librarian_agent(collection, query, filters=None, n_results=5):
    """
    Librarian Agent — searches local ChromaDB vector store
    and uses Groq LLM to generate structured school summaries.

    Returns:
        dict with keys:
            - schools   : list of matched school metadata
            - summary   : LLM-generated comparison summary
            - has_data  : True if local results were found
    """
    print(f"\n📚 Librarian Agent activated for: '{query}'")

    # ── Step 1: Semantic search in ChromaDB ───────
    results = query_vector_db(
        collection,
        query,
        filters=filters,
        n_results=n_results
    )

    schools   = results.get("metadatas", [[]])[0]
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not schools:
        print("   ℹ️ No local results found.")
        return {
            "schools":  [],
            "summary":  "",
            "has_data": False
        }

    print(f"   ✅ Found {len(schools)} schools in local database.")

    # ── Step 2: Build context for LLM ─────────────
    school_context = ""
    for i, (doc, dist) in enumerate(zip(documents, distances)):
        match_score    = round((1 - dist) * 100, 1)
        school_context += f"\n--- School {i+1} (Match: {match_score}%) ---\n"
        school_context += doc + "\n"

    # ── Step 3: Chain-of-Thought prompt ───────────
    cot_prompt = f"""
You are EduNavigator AI, an expert educational consultant.
A user is searching for: "{query}"

Here are the matching schools from our database:
{school_context}

Using Chain-of-Thought reasoning, analyze these schools by:
1. IDENTIFY the most relevant schools for this specific query
2. COMPARE key factors: rating, tuition, programs, class size
3. HIGHLIGHT standout features that match the user's query
4. RECOMMEND the top choice with a clear reason

Provide a concise, helpful summary in this format:

**Top Match:** [School Name]
**Why:** [2-3 sentences explaining why it best matches the query]

**Quick Comparison:**
- [School 1]: [One line highlight]
- [School 2]: [One line highlight]
- [School 3]: [One line highlight]

**Pro Tip:** [One practical advice for the user]

Keep the total response under 200 words. Be specific and helpful.
"""

    # ── Step 4: Get LLM summary ────────────────────
    print("   🤖 Generating AI summary...")
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EduNavigator AI, a helpful and knowledgeable "
                        "educational consultant. Give concise, accurate, and "
                        "practical advice to students and parents."
                    )
                },
                {
                    "role": "user",
                    "content": cot_prompt
                }
            ],
            max_tokens=400,
            temperature=0.3
        )
        summary = response.choices[0].message.content
        print("   ✅ AI summary generated.")
    except Exception as e:
        summary = f"Summary unavailable: {e}"
        print(f"   ❌ LLM error: {e}")

    return {
        "schools":  schools,
        "summary":  summary,
        "has_data": True
    }