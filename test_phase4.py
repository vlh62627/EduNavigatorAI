import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from utils.embeddings import load_vector_db
from agents.librarian_agent    import librarian_agent
from agents.researcher_agent   import researcher_agent
from agents.doc_specialist_agent import doc_specialist_agent

print("=" * 55)
print("   Phase 4 Test — Three AI Agents")
print("=" * 55)

# ── Load Vector DB ─────────────────────────────────
print("\n🔄 Loading vector database...")
collection = load_vector_db()

# ── Test 1: Librarian Agent ────────────────────────
print("\n" + "=" * 55)
print("TEST 1 — Librarian Agent (Local RAG)")
print("=" * 55)
result = librarian_agent(
    collection,
    query   = "best high school with AP courses and clubs",
    filters = {"state": "Texas", "level": "High School"},
    n_results = 3
)
print(f"\nSchools found : {len(result['schools'])}")
print(f"Has data      : {result['has_data']}")
print(f"\nAI Summary:\n{result['summary']}")

# ── Test 2: Researcher Agent ───────────────────────
print("\n" + "=" * 55)
print("TEST 2 — Researcher Agent (Live Web Search)")
print("=" * 55)
result2 = researcher_agent(
    query = "UT Austin admission requirements tuition fees",
    state = "Texas",
    level = "University"
)
print(f"\nWeb results found : {len(result2['web_results'])}")
print(f"\nSources:")
for s in result2["sources"][:3]:
    print(f"   - {s['title'][:60]}")
    print(f"     {s['url']}")
print(f"\nAI Summary:\n{result2['summary']}")

# ── Test 3: Doc Specialist Agent ───────────────────
print("\n" + "=" * 55)
print("TEST 3 — Doc Specialist Agent (PDF Checklist)")
print("=" * 55)
result3 = doc_specialist_agent(
    school_name   = "University of Texas Austin",
    level         = "University",
    state         = "Texas",
    extra_context = "Engineering major, needs financial aid info"
)
print(f"\nPDF saved to : {result3['filepath']}")
print(f"Total items  : {sum(len(v) for v in result3['checklist'].values())}")
print(f"\nChecklist sections:")
for section, items in result3["checklist"].items():
    print(f"\n  [{section}]")
    for item in items:
        print(f"   ☐ {item}")
print(f"\nPro Tips:")
for i, tip in enumerate(result3["tips"], 1):
    print(f"   {i}. {tip}")

print("\n" + "=" * 55)
print("✅ Phase 4 Complete! All three agents working.")
print("=" * 55)