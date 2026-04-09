import os
from dotenv import load_dotenv
load_dotenv()

print(f"TAVILY_API_KEY = '{os.getenv('TAVILY_API_KEY')}'")
print(f"GROQ_API_KEY   = '{os.getenv('GROQ_API_KEY')[:10]}...'")