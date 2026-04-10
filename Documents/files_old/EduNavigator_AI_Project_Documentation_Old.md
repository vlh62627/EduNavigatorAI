# EduNavigator AI — Complete Project Documentation
**Agentic RAG Framework for Hyper-Local Academic Mapping**
Generated: April 2026

---

## Table of Contents
1. Project Overview
2. Technology Stack
3. Project Setup (Phase 1)
4. Data Layer (Phase 2)
5. Streamlit UI (Phase 3)
6. AI Agents (Phase 4)
7. Agent Orchestrator (Phase 5)
8. Full App Integration (Phase 6)
9. Government API Integration (Phase 7)
10. Complete File Structure
11. All Source Code
12. Issues Encountered & Fixes
13. Current Status

---

## 1. Project Overview

**EduNavigator AI** is an intelligent educational discovery platform built on an Agentic RAG (Retrieval-Augmented Generation) architecture. It helps students and parents find schools and universities across all 50 US states — from preschools to medical schools — through a coordinated multi-agent AI system.

### Problem Solved
- Information fragmentation across multiple sources
- Outdated static data on fees and requirements
- Zero personalization in existing school search tools
- Missing county/ISD level data for K-12 schools

### Solution
Three specialized AI agents coordinated by an Orchestrator:
- **Librarian Agent** — Local ChromaDB vector search
- **Researcher Agent** — Live Tavily web search
- **Document Specialist Agent** — PDF checklist generation

---

## 2. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend UI | Streamlit 1.35 | Web interface |
| LLM Engine | Groq llama-3.3-70b-versatile | AI reasoning |
| Vector Database | ChromaDB | Local semantic search + cache |
| Embedding Model | sentence-transformers all-MiniLM-L6-v2 | 384-dim embeddings |
| Web Search | Tavily API | Live web research |
| PDF Generation | FPDF2 | Application checklists |
| University Data | College Scorecard API | US university data |
| K-12 Data | NCES CCD Database | 98,957 schools all 50 states |
| Data Processing | Pandas | CSV and data handling |
| Environment | Python 3.11, venv | Runtime |

### Free API Keys Required
- **Groq**: https://console.groq.com (free, no credit card)
- **Tavily**: https://tavily.com (free tier 1000/month)
- **College Scorecard**: https://api.data.gov/signup (free)

---

## 3. Project Setup (Phase 1)

### Environment Setup
```cmd
mkdir EduNavigatorAI
cd EduNavigatorAI
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### requirements.txt
```
streamlit==1.35.0
groq==0.9.0
langchain==0.2.6
langchain-groq==0.1.6
langchain-community==0.2.6
chromadb==0.5.3
sentence-transformers==3.0.1
tavily-python==0.3.3
fpdf2==2.7.9
pandas==2.2.2
python-dotenv==1.0.1
requests==2.32.3
```

### .env Configuration
```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
COLLEGE_SCORECARD_API_KEY=your_college_scorecard_api_key_here

GROQ_MODEL=llama-3.3-70b-versatile
EMBED_MODEL=all-MiniLM-L6-v2
CHROMA_DB_PATH=./chroma_db
OUTPUT_PATH=./outputs

ANONYMIZED_TELEMETRY=False
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### Project Folder Structure
```
EduNavigatorAI/
├── app.py
├── .env
├── requirements.txt
├── data/
│   ├── schools.csv          (50 curated schools)
│   ├── nces_schools.csv     (downloaded NCES CCD file)
│   └── k12_schools.csv      (processed 98,957 schools)
├── agents/
│   ├── librarian_agent.py
│   ├── researcher_agent.py
│   ├── doc_specialist_agent.py
│   └── orchestrator.py
├── utils/
│   ├── embeddings.py
│   ├── geo_filter.py
│   ├── pdf_generator.py
│   ├── college_scorecard_api.py
│   ├── nces_api.py
│   └── build_k12_database.py
└── outputs/
```

### Windows-Specific Issues & Fixes
- **PowerShell execution policy**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **rmdir command**: Use `rmdir /s /q foldername` in CMD or `Remove-Item -Recurse -Force foldername` in PowerShell
- **Python 3.14 compatibility**: Use Python 3.11 — `py -3.11 -m venv venv`
- **Paging file too small**: Increase Windows virtual memory to 4096-8192 MB
- **Groq model decommissioned**: Use `llama-3.3-70b-versatile` not `llama3-70b-8192`

---

## 4. Data Layer (Phase 2)

### Geographic Filter Logic
- **University / Community College / Medical School** → State level only (no county)
- **High School / Elementary / Middle School / Preschool** → State → County cascade

### Education Levels
```python
["Preschool", "Elementary", "Middle School", "High School",
 "Community College", "University", "Medical School"]
```

### ChromaDB Vector Store
- Cosine similarity distance metric
- HNSW indexing
- Persistent local storage
- Dual purpose: CSV embeddings + API result cache

---

## 5. Streamlit UI (Phase 3)

### Filter Flow
```
Step 1: Select Education Level
Step 2: Select State (all 50 US states)
Step 3: Select County (K-12 only, disabled for University/College)
        ↓
Search Button → Results display
```

### Key UX Decisions
- Search button must be clicked — no auto-trigger on dropdown change
- County filter disabled for University/Community College/Medical School
- Button disabled until both Level and State are selected
- No internal system messages shown to user — results only

---

## 6. AI Agents (Phase 4)

### Librarian Agent (librarian_agent.py)
- Searches ChromaDB with semantic similarity
- Uses Chain-of-Thought prompting for school comparison
- Returns top match, quick comparison, pro tip
- Model: Groq llama-3.3-70b-versatile, temp=0.3, max_tokens=400

### Researcher Agent (researcher_agent.py)
- Uses Tavily API advanced search
- Synthesizes web results with LLM
- Returns structured school data from live web
- Model: Groq llama-3.3-70b-versatile, temp=0.2, max_tokens=500

### Document Specialist Agent (doc_specialist_agent.py)
- Generates JSON checklist via LLM
- Builds PDF with FPDF2 (color-coded sections)
- 5 sections: Academic, Personal, Application, Financial, Deadlines
- Falls back to hardcoded checklist if LLM fails
- Fixes: Replace `—` with `-` (Helvetica font limitation)

---

## 7. Agent Orchestrator (Phase 5)

### Decision Logic
```
User Query + Filters
        ↓
1. Check local CSV data (has_local_data)
2. Check ChromaDB cache (is_cached)
        ↓
   Cache HIT → Librarian Agent (instant)
   Cache MISS + Local data → Librarian Agent
   No local data + University level → College Scorecard API
   No local data + K-12 level → NCES CCD Database / Tavily
   Specific school keyword → Researcher Agent (web)
   PDF requested → Doc Specialist Agent
        ↓
   Cache API results in ChromaDB for next time
```

### Specific School Keywords
```python
["ut austin", "harvard", "stanford", "mit", "yale",
 "princeton", "texas tech", "baylor", "rice university",
 "tcu", "duke", "vanderbilt", "georgetown", "notre dame",
 "emory", "tulane", "ohio state", "penn state", "purdue",
 "georgia tech", "virginia tech", "arizona state"]
```

---

## 8. Full App Integration (Phase 6)

### Data Sources Summary
| Education Level | Data Source |
|---|---|
| University | College Scorecard API (live) |
| Community College | College Scorecard API (live) |
| Medical School | College Scorecard API (live) |
| High School | NCES CCD Database (98,957 schools) |
| Elementary | NCES CCD Database (98,957 schools) |
| Middle School | NCES CCD Database (98,957 schools) |
| Preschool | NCES CCD Database (98,957 schools) |
| Any (fallback) | Tavily web search |
| Specific schools | Tavily web search |

### Platform Stats (Accurate)
- Schools Available: 100,000+
- States Covered: All 50
- Education Levels: 7
- Data Sources: 3 Live APIs

---

## 9. Government API Integration (Phase 7)

### College Scorecard API
- Endpoint: https://api.data.gov/ed/collegescorecard/v1/schools
- Free API key from https://api.data.gov/signup
- Filters: state, degree level, school ownership
- Returns: name, city, tuition in/out state, acceptance rate, student size

### NCES CCD Database (Local)
- Downloaded from: https://nces.ed.gov/ccd/files.asp
- File: Public Elementary/Secondary School Universe Survey 2022-23
- Processed: 98,957 active schools across all 50 states
- Columns used: SCH_NAME, ST, LEA_NAME, LCITY, GSLO, GSHI, WEBSITE, SY_STATUS

### NCES CCD Processing
```
Download nces_schools.csv
        ↓
python utils/build_k12_database.py
        ↓
Outputs data/k12_schools.csv (22.2 MB, 98,957 schools)
```

### NCES CCD Results by State (Top 10)
```
California    10,265 schools
Texas          9,046 schools
New York       4,769 schools
Illinois       4,360 schools
Florida        4,142 schools
Ohio           3,509 schools
Michigan       3,447 schools
Pennsylvania   2,915 schools
North Carolina 2,682 schools
Minnesota      2,622 schools
```

### Known Issues in NCES File
- County column: Not found in current download (column name varies by year)
- Charter/Magnet: Not found (need exact column name from full column list)
- Student count: Not found (MEMBER column may be in separate file)
- Fix: Run updated build_k12_database.py which prints all 65 column names

---

## 10. Complete File Structure

### utils/geo_filter.py — Key Functions
```python
get_all_states()           # All 50 US states
get_education_levels()     # 7 levels including Medical School
is_county_applicable(level)# True for K-12, False for university
get_counties_for_level()   # Counties from local CSV
has_local_data()           # Check if state+level in CSV
filter_schools()           # Apply filters to CSV dataframe
get_filter_summary()       # Human-readable filter description
```

### utils/embeddings.py — Key Functions
```python
get_embed_model()          # Lazy load sentence transformer
load_vector_db()           # Load/build ChromaDB
query_vector_db()          # Semantic search
cache_api_schools()        # Store API results in ChromaDB
is_cached()                # Check ChromaDB cache
get_cache_stats()          # Cache statistics
```

### utils/college_scorecard_api.py — Key Functions
```python
fetch_universities()       # Fetch from College Scorecard API
get_state_abbreviation()   # Convert state name to abbreviation
```

### utils/nces_api.py — Key Functions
```python
fetch_k12_schools()        # Main entry: local DB first, web fallback
_get_from_local_db()       # Query data/k12_schools.csv
_build_description()       # Clean description without double words
_tavily_k12_search()       # Web search fallback
_extract_school_names()    # Parse school names from web content
_fallback_from_titles()    # Last resort from search titles
```

### utils/build_k12_database.py — Key Functions
```python
process_ccd_file()         # Convert NCES CSV to our schema
get_k12_by_state_level()   # Query the processed database
grade_to_level()           # Map NCES grades to education level
build_description()        # Build school description
find_column()              # Find column with multiple name candidates
```

---

## 11. All Source Code Files

### agents/orchestrator.py
See full code in conversation — handles 4-step agent routing:
1. Librarian Agent (local/cache)
2. College Scorecard API (university levels)
3. NCES/Tavily (K-12 levels)
4. Doc Specialist (PDF generation)

### agents/librarian_agent.py
Chain-of-Thought RAG agent using ChromaDB + Groq

### agents/researcher_agent.py
Tavily web search + Groq synthesis agent

### agents/doc_specialist_agent.py
FPDF2 PDF checklist generator with Groq JSON output

---

## 12. Issues Encountered & Fixes

| Issue | Root Cause | Fix |
|---|---|---|
| `proxies` error in Groq | Version conflict with httpx | `pip install httpx==0.27.0 groq==0.9.0` |
| Model decommissioned | llama3-70b-8192 retired | Use `llama-3.3-70b-versatile` |
| ChromaDB telemetry warnings | Known Windows bug in ChromaDB | Harmless — ignore |
| Paging file too small | Windows virtual memory | Increase to 4096-8192 MB |
| `—` character in PDF | Helvetica doesn't support em-dash | Replace `—` with `-` |
| HTML rendering in cards | F-string triple quotes | Use string concatenation |
| NCES API timeout | GIS REST API blocks Python requests | Use Tavily fallback instead |
| `_embed_model` not defined | Module-level variable in Streamlit | Use lazy `get_embed_model()` |
| County not showing | NCES file uses different column name | Print all columns, find exact name |
| Double "school" in description | Template + level name repeated | Regex clean + `_build_description()` |
| PowerShell `rmdir /s /q` fails | Wrong terminal type | Use `Remove-Item -Recurse -Force` |
| `venv` deactivates | New terminal opened | Always run `venv\Scripts\activate` |

---

## 13. Current Status

### Completed ✅
- Phase 1: Full environment setup
- Phase 2: Data layer with ChromaDB
- Phase 3: Streamlit UI with smart filters
- Phase 4: All three AI agents working
- Phase 5: Orchestrator with smart routing
- Phase 6: Full app integration
- Phase 7: College Scorecard API + NCES CCD database
- 98,957 K-12 schools processed from NCES CCD
- Medical School as new education level
- ChromaDB as smart cache layer
- Clean UI — no internal messages

### In Progress 🔄
- Finding exact county/charter/student column names in NCES file
- Adding county display to K-12 school cards

### Pending
- Run updated build_k12_database.py to see all 65 column names
- Map correct county column to get proper county display
- Final UI polish and capstone presentation

---

## Next Steps

1. Run `python utils/build_k12_database.py` to see all column names
2. Update `CCD_COLUMN_CANDIDATES` with correct county/charter/student columns
3. Rebuild `data/k12_schools.csv` with county data
4. Final testing across all 50 states
5. Prepare capstone presentation

---

*EduNavigator AI — Built with Python, Streamlit, Groq, ChromaDB, Tavily, College Scorecard API, and NCES CCD data.*
