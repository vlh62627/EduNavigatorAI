# EduNavigator AI — Complete Project Documentation
**Agentic RAG Framework for Hyper-Local Academic Mapping**
**Version 2.0 — Final | April 2026**

---

## Table of Contents
1. Project Overview
2. Technology Stack
3. Architecture
4. Data Sources
5. File Structure
6. Agent System
7. Filter System
8. Deployment
9. Issues & Fixes
10. Current Status

---

## 1. Project Overview

**EduNavigator AI** is an intelligent educational discovery platform built on an Agentic RAG architecture. It helps students and parents find schools and universities across all 50 US states — from Preschool to Medical School — through a coordinated multi-agent AI system.

**Live URL:** https://edunavigatorai.streamlit.app
**GitHub:** https://github.com/vlh62627/EduNavigatorAI

### Problem Solved
- Information fragmentation across multiple sources
- Outdated static data on fees and requirements
- Zero personalization in existing school search tools
- Missing district/ISD level data for K-12 schools

### Solution
Three specialized AI agents coordinated by an Orchestrator:
- **Librarian Agent** — Local ChromaDB vector search
- **Researcher Agent** — Live Tavily web search
- **Document Specialist Agent** — PDF checklist generation

---

## 2. Technology Stack

| Component | Technology | Version |
|---|---|---|
| Frontend UI | Streamlit | 1.35.0 |
| LLM Engine | Groq LLaMA 3.3 | llama-3.3-70b-versatile |
| Vector Database | ChromaDB | 0.5.3 |
| Embedding Model | ChromaDB Default (onnx) | all-MiniLM-L6-v2 |
| Web Search | Tavily API | 0.7.23 |
| PDF Generation | FPDF2 | 2.7.9 |
| University Data | College Scorecard API | Free |
| K-12 Data | NCES CCD 2022-23 | 98,957 schools |
| Data Processing | Pandas | 2.2.x |
| Runtime | Python | 3.11 |

### Free API Keys Used
- **Groq**: https://console.groq.com
- **Tavily**: https://app.tavily.com
- **College Scorecard**: https://api.data.gov/signup

---

## 3. Architecture

### Orchestrator Decision Flow
```
User Query + Filters (Level, State, District, City)
        ↓
K-12 Level?
  YES → Always fetch from NCES database (bypass cache)
  NO  → Check ChromaDB cache
          Cache HIT  → Librarian Agent
          Cache MISS → College Scorecard API → Cache results
        ↓
Specific school keyword? → Researcher Agent (Tavily)
PDF requested?           → Doc Specialist Agent
        ↓
Return combined results to UI
```

### Education Levels
```
Preschool → Elementary → Middle School → High School
Community College → University → Medical School
```

### Filter Cascade
```
Step 1: Education Level
Step 2: State (all 50)
Step 3: County / District (K-12 only — shows ISD/district names)
Step 4: City (optional, within district)
```

---

## 4. Data Sources

### NCES CCD 2022-23 (K-12)
- **Source**: https://nces.ed.gov/ccd/files.asp
- **File**: Public Elementary/Secondary School Universe Survey
- **Processed**: 98,957 active schools
- **Columns used**: SCH_NAME, ST, LEA_NAME, LCITY, LZIP, LEVEL, SCH_TYPE, CHARTER_TEXT, WEBSITE, SY_STATUS
- **County derived from**: LZIP → zip_county.csv (33,048 ZIP codes, 96% coverage)

### NCES Level Mapping
```
"Elementary"     → Elementary
"Middle"         → Middle School
"High"           → High School
"Prekindergarten"→ Preschool
"Secondary"      → High School
```

### College Scorecard API (University/College/Medical)
- **Endpoint**: https://api.data.gov/ed/collegescorecard/v1/schools
- **Filters**: state, degree level, ownership
- **Medical filter**: 20+ health keywords including icahn, weill, grossman, feinberg etc.

### Coverage by State (Top 10)
```
California    10,265    Texas          9,046
New York       4,769    Illinois       4,360
Florida        4,142    Ohio           3,509
Michigan       3,447    Pennsylvania   2,915
North Carolina 2,682    Minnesota      2,622
```

---

## 5. File Structure

```
EduNavigatorAI/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── packages.txt                # System packages (libjpeg-dev etc.)
├── .python-version             # Forces Python 3.11 on Streamlit Cloud
├── .streamlit/
│   └── config.toml             # Theme and server config
├── .gitignore                  # Excludes env, nces_schools.csv
├── data/
│   ├── schools.csv             # 50 curated schools (in git)
│   ├── k12_schools.csv         # 98,957 NCES schools (in git, 25MB)
│   ├── zip_county.csv          # 33,048 ZIP→county mappings
│   └── nces_schools.csv        # Raw NCES download (NOT in git)
├── agents/
│   ├── orchestrator.py         # Master controller
│   ├── librarian_agent.py      # RAG agent (ChromaDB)
│   ├── researcher_agent.py     # Web search agent (Tavily)
│   └── doc_specialist_agent.py # PDF checklist agent
├── utils/
│   ├── embeddings.py           # ChromaDB vector store
│   ├── geo_filter.py           # Geographic filtering + district lookup
│   ├── nces_api.py             # K-12 local DB + web fallback
│   ├── college_scorecard_api.py# University/Medical API
│   ├── build_k12_database.py   # NCES CSV processor
│   ├── startup.py              # Ensures data files on deploy
│   └── pdf_generator.py        # PDF utilities
└── outputs/                    # Generated PDFs
```

---

## 6. Agent System

### Librarian Agent
- Searches ChromaDB with semantic similarity
- Chain-of-Thought prompting for school comparison
- Returns: top match, quick comparison, pro tip
- Model: llama-3.3-70b-versatile, temp=0.3, max_tokens=400

### Researcher Agent
- Uses Tavily API 0.7.23 (upgraded from 0.3.3)
- Synthesizes web results with LLM
- Returns structured school data from live web
- Only fires when NCES/API returns no results or specific school queried
- Model: llama-3.3-70b-versatile, temp=0.2, max_tokens=500

### Doc Specialist Agent
- Generates JSON checklist via LLM
- Builds PDF with FPDF2 (color-coded sections)
- 5 sections: Academic, Personal, Application, Financial, Deadlines
- Replaces em-dash with hyphen (Helvetica font limitation)

---

## 7. Filter System

### District Filter Logic
The County/District filter uses `district` column from k12_schools.csv (more meaningful than county):
- **Texas**: Shows FRISCO ISD, PLANO ISD, MCKINNEY ISD etc.
- **California**: Shows Acton-Agua Dulce Unified, Ross Valley Elementary etc.
- **New York**: Shows DOLGEVILLE CENTRAL SCHOOL DISTRICT etc.
- **Alabama**: Shows Hoover City, Madison City etc.

### City Filter Logic
Cities are populated based on selected district — allows searching within Frisco ISD → Frisco, TX specifically.

### Filter not applicable for
- University, Community College, Medical School → State level only

---

## 8. Deployment

### Streamlit Community Cloud
- **URL**: https://edunavigatorai.streamlit.app
- **Runtime**: Python 3.11 (via .python-version file)
- **Secrets**: Added via Streamlit Cloud dashboard

### Secrets Required
```toml
GROQ_API_KEY = "..."
TAVILY_API_KEY = "..."
COLLEGE_SCORECARD_API_KEY = "..."
GROQ_MODEL = "llama-3.3-70b-versatile"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHROMA_DB_PATH = "./chroma_db"
OUTPUT_PATH = "./outputs"
ANONYMIZED_TELEMETRY = "False"
```

### requirements.txt (Final)
```
streamlit==1.35.0
groq==0.9.0
langchain==0.2.6
langchain-groq==0.1.6
langchain-community==0.2.6
chromadb==0.5.3
tavily-python==0.7.23
fpdf2==2.7.9
Pillow==10.3.0
pandas>=2.0.0
numpy==1.26.4
python-dotenv==1.0.1
requests==2.32.3
httpx==0.27.0
```

### packages.txt
```
build-essential
libjpeg-dev
zlib1g-dev
libpng-dev
```

---

## 9. Issues & Fixes

| Issue | Root Cause | Fix |
|---|---|---|
| Groq model retired | llama3-70b-8192 decommissioned | Use llama-3.3-70b-versatile |
| sentence-transformers 2GB | torch dependency too large | Use ChromaDB DefaultEmbeddingFunction (onnx) |
| Python 3.14 on cloud | Streamlit Cloud default | Add .python-version with "3.11" |
| Pillow build fail | Missing system libs | Add packages.txt with libjpeg-dev etc. |
| NCES API timeout | GIS REST API blocked Python | Use local NCES CCD CSV database |
| ChromaDB cache bypassing NCES | K-12 cache hit skipped fresh fetch | Force K-12 to always use NCES |
| Tavily 401 | Outdated SDK (0.3.3) | Upgrade to tavily-python==0.7.23 |
| Medical school empty | Strict health keyword filter | Expanded to 20+ health keywords |
| County not in NCES file | Directory file has no county col | Derive from LZIP via zip_county.csv |
| NCES level wrong | Assumed numeric codes | LEVEL column uses text: Elementary/High/Middle |
| District not showing | Using county instead | Switched to LEA_NAME (district) column |
| k12_schools.csv not on cloud | In .gitignore | Removed from .gitignore, pushed to GitHub |
| API Keys.txt committed | Accidental git add | Deleted repo, fresh push without secrets |
| pandas==2.2.2 builds from source | No wheel for Python 3.14 | Changed to pandas>=2.0.0 |

---

## 10. Current Status

### Completed ✅
- Phase 1: Environment setup
- Phase 2: Data layer + ChromaDB
- Phase 3: Streamlit UI with smart filters
- Phase 4: Three AI agents
- Phase 5: Orchestrator with smart routing
- Phase 6: Full app integration
- Phase 7: College Scorecard + NCES CCD APIs
- District/ISD filtering (FRISCO ISD, PLANO ISD etc.)
- City sub-filter within district
- Medical school expanded keyword filter
- ChromaDB DefaultEmbeddingFunction (no torch)
- Live on Streamlit Community Cloud
- 98,957 K-12 schools in GitHub repo

### Platform Stats
- Schools: 100,000+
- States: All 50
- Education Levels: 7
- Live APIs: 3 (Groq, Tavily, College Scorecard)
- Deployment: Streamlit Community Cloud

---

*EduNavigator AI — Built with Python 3.11, Streamlit, Groq LLaMA 3.3, ChromaDB, Tavily, NCES CCD, College Scorecard API*
*Capstone Project | April 2026*
