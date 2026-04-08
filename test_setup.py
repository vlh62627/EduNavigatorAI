import os
from dotenv import load_dotenv

load_dotenv()

print("=== EduNavigator AI — Setup Test ===\n")

# Test 1: API Keys
groq_key = os.getenv("GROQ_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")
print(f"✅ GROQ_API_KEY loaded: {'Yes' if groq_key else 'NO - Check .env'}")
print(f"✅ TAVILY_API_KEY loaded: {'Yes' if tavily_key else 'NO - Check .env'}")

# Test 2: Groq LLM
print("\n--- Testing Groq LLM ---")
try:
    from groq import Groq
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say: EduNavigator setup successful!"}],
        max_tokens=20
    )
    print(f"✅ Groq response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Groq error: {e}")

# Test 3: ChromaDB
print("\n--- Testing ChromaDB ---")
try:
    import chromadb
    client = chromadb.Client()
    col = client.create_collection("test")
    col.add(documents=["test doc"], ids=["1"])
    results = col.query(query_texts=["test"], n_results=1)
    print(f"✅ ChromaDB working: {results['documents'][0][0]}")
    client.delete_collection("test")
except Exception as e:
    print(f"❌ ChromaDB error: {e}")

# Test 4: Sentence Transformers
print("\n--- Testing Embeddings ---")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = model.encode("test sentence")
    print(f"✅ Embeddings working. Vector size: {len(embedding)}")
except Exception as e:
    print(f"❌ Embeddings error: {e}")

# Test 5: Tavily
print("\n--- Testing Tavily Search ---")
try:
    from tavily import TavilyClient
    t = TavilyClient(api_key=tavily_key)
    result = t.search("best high schools in Texas", max_results=1)
    print(f"✅ Tavily working: {result['results'][0]['title'][:60]}...")
except Exception as e:
    print(f"❌ Tavily error: {e}")

print("\n=== Test Complete ===")