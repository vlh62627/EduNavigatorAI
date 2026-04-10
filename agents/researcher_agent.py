import os
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def researcher_agent(query, state=None, level=None, n_results=5):
    """
    Researcher Agent — searches the web live using Tavily
    when local ChromaDB data is missing or insufficient.

    Returns:
        dict with keys:
            - web_results : raw Tavily search results
            - summary     : LLM-generated summary from web data
            - sources     : list of source URLs found
    """
    # ── Initialize clients fresh each call ────────
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    tavily      = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    print(f"\n🔍 Researcher Agent activated for: '{query}'")

    # ── Step 1: Build targeted search query ───────
    location_context = ""
    if state:
        location_context += f" in {state}"
    if level:
        location_context += f" {level}"

    search_query = (
        f"{query}{location_context} "
        f"ratings fees admission requirements 2024"
    )
    print(f"   🌐 Searching web for: '{search_query}'")

    # ── Step 2: Tavily web search ──────────────────
    try:
        search_results = tavily.search(
            query       = search_query,
            max_results = n_results
        )
        web_results = search_results.get("results", [])
        print(f"   ✅ Found {len(web_results)} web results.")
    except Exception as e:
        print(f"   ❌ Tavily error: {e}")
        return {
            "web_results": [],
            "summary":     f"Web search failed: {e}",
            "sources":     []
        }

    if not web_results:
        return {
            "web_results": [],
            "summary":     "No web results found.",
            "sources":     []
        }

    # ── Step 3: Build context from web results ────
    web_context = ""
    sources     = []
    for i, result in enumerate(web_results):
        web_context += f"\n--- Source {i+1} ---\n"
        web_context += f"Title  : {result.get('title',   'N/A')}\n"
        web_context += f"URL    : {result.get('url',     'N/A')}\n"
        web_context += f"Content: {result.get('content', 'N/A')[:500]}\n"
        sources.append({
            "title": result.get("title", "N/A"),
            "url":   result.get("url",   "N/A")
        })

    # ── Step 4: Chain-of-Thought LLM synthesis ────
    cot_prompt = f"""
You are EduNavigator AI, an expert educational researcher.
A user is looking for: "{query}"
Location context: {location_context if location_context else "Not specified"}

I searched the web and found these results:
{web_context}

Using Chain-of-Thought reasoning:
1. EXTRACT key facts about schools mentioned (name, location, ratings, fees)
2. IDENTIFY the most relevant institutions for this query
3. SYNTHESIZE the information into actionable insights
4. HIGHLIGHT any scholarships, deadlines, or special programs mentioned

Provide your response in this format:

**Schools Found Online:**
- [School Name] | [Location] | [Key fact about rating or fee]
- [School Name] | [Location] | [Key fact about rating or fee]

**Key Insights:**
[2-3 sentences summarizing the most important findings]

**Important Deadlines/Requirements:**
[Any deadlines or requirements found in the search results]

**Recommended Next Steps:**
[2 practical steps the user should take]

Keep response under 250 words. Be specific and factual.
"""

    print("   🤖 Synthesizing web results with AI...")
    try:
        response = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = [
                {
                    "role": "system",
                    "content": (
                        "You are EduNavigator AI, a thorough educational "
                        "researcher. Extract and synthesize accurate "
                        "information from web sources to help students "
                        "and parents make informed decisions."
                    )
                },
                {
                    "role": "user",
                    "content": cot_prompt
                }
            ],
            max_tokens  = 500,
            temperature = 0.2
        )
        summary = response.choices[0].message.content
        print("   ✅ Web research summary generated.")
    except Exception as e:
        summary = f"Summary unavailable: {e}"
        print(f"   ❌ LLM error: {e}")

    return {
        "web_results": web_results,
        "summary":     summary,
        "sources":     sources
    }