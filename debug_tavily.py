import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

key = os.getenv("TAVILY_API_KEY")
print(f"Key: {key[:20]}...")

try:
    client = TavilyClient(api_key=key)
    result = client.search("best high schools in Texas", max_results=1)
    print(f"✅ Tavily working: {result['results'][0]['title']}")
except Exception as e:
    print(f"❌ Tavily error: {e}")