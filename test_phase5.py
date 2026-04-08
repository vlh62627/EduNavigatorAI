import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from utils.embeddings import load_vector_db
from agents.orchestrator import orchestrator

print("=" * 55)
print("   Phase 5 Test — Agent Orchestrator")
print("=" * 55)

# ── Load Vector DB ─────────────────────────────────
print("\n🔄 Loading vector database...")
collection = load_vector_db()

# ══════════════════════════════════════════════════
# TEST 1 — Local data sufficient (Librarian only)
# ══════════════════════════════════════════════════
print("\n\nTEST 1 — Query with sufficient local data")
print("-" * 55)
result1 = orchestrator(
    collection = collection,
    query      = "best high school with AP courses",
    state      = "Texas",
    level      = "High School",
    county     = "Collin",
    n_results  = 3
)
print(f"\n✅ Source        : {result1['source']}")
print(f"✅ Agents called : {result1['agents_called']}")
print(f"✅ Schools found : {len(result1['schools'])}")
print(f"\nLocal Summary:\n{result1['local_summary']}")

# ══════════════════════════════════════════════════
# TEST 2 — Specific school triggers web search
# ══════════════════════════════════════════════════
print("\n\nTEST 2 — Specific school not in local DB")
print("-" * 55)
result2 = orchestrator(
    collection = collection,
    query      = "UT Austin computer science program fees",
    state      = "Texas",
    level      = "University",
    n_results  = 3
)
print(f"\n✅ Source        : {result2['source']}")
print(f"✅ Agents called : {result2['agents_called']}")
print(f"✅ Web sources   : {len(result2['web_sources'])}")
print(f"\nWeb Summary:\n{result2['web_summary']}")

# ══════════════════════════════════════════════════
# TEST 3 — Full pipeline with PDF generation
# ══════════════════════════════════════════════════
print("\n\nTEST 3 — Full pipeline with PDF checklist")
print("-" * 55)
result3 = orchestrator(
    collection   = collection,
    query        = "Plano Senior High admission requirements",
    state        = "Texas",
    level        = "High School",
    n_results    = 3,
    generate_pdf = True,
    school_name  = "Plano Senior High"
)
print(f"\n✅ Source        : {result3['source']}")
print(f"✅ Agents called : {result3['agents_called']}")
if result3["pdf_result"]:
    print(f"✅ PDF saved to  : {result3['pdf_result']['filepath']}")
    print(f"✅ Total items   : {sum(len(v) for v in result3['pdf_result']['checklist'].values())}")

# ══════════════════════════════════════════════════
# TEST 4 — No filters (broad search)
# ══════════════════════════════════════════════════
print("\n\nTEST 4 — Broad search across all Texas universities")
print("-" * 55)
result4 = orchestrator(
    collection = collection,
    query      = "affordable university with scholarships and engineering",
    state      = "Texas",
    level      = "University",
    n_results  = 5
)
print(f"\n✅ Source        : {result4['source']}")
print(f"✅ Agents called : {result4['agents_called']}")
print(f"✅ Schools found : {len(result4['schools'])}")
print(f"\nLocal Summary:\n{result4['local_summary']}")

print("\n" + "=" * 55)
print("✅ Phase 5 Complete! Orchestrator working.")
print("=" * 55)