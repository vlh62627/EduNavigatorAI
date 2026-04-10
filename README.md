# 🎓 EduNavigator AI

**Agentic RAG Framework for Hyper-Local Academic Mapping**

> Intelligent School & University Discovery — All 50 US States

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://edunavigatorai.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌐 Live Demo

**👉 [https://edunavigatorai.streamlit.app](https://edunavigatorai.streamlit.app)**

---

## 📌 What is EduNavigator AI?

EduNavigator AI is an intelligent educational discovery platform that helps students and parents find the right school or university across all 50 US states — from Preschool to Medical School.

Unlike a Google Search that returns 10 blue links, EduNavigator AI delivers:

- ✅ Structured school cards with tuition, enrollment, and programs
- ✅ AI-powered comparison and recommendations
- ✅ Filter by State → District/ISD → City
- ✅ Live data from 3 government APIs
- ✅ Downloadable PDF application checklists

---

## 🏗️ Architecture

EduNavigator AI uses a **Multi-Agent RAG (Retrieval-Augmented Generation)** system with 3 specialized AI agents coordinated by a smart orchestrator:

```
User Query + Filters
        ↓
    Orchestrator
   ┌──────┬──────┬──────┐
   ↓      ↓      ↓      ↓
📚      🔍      📄    💾
Librarian  Researcher  Doc     ChromaDB
Agent      Agent    Specialist  Cache
(ChromaDB) (Tavily)  (PDF)
```

### Agents

| Agent | Role | Technology |
|---|---|---|
| 📚 Librarian Agent | Semantic search on local vector database | ChromaDB + Groq |
| 🔍 Researcher Agent | Live web search for real-time results | Tavily + Groq |
| 📄 Doc Specialist | AI-generated PDF application checklists | FPDF2 + Groq |

---

## 📊 Platform Scale

| Metric | Value |
|---|---|
| Total Schools | 100,000+ |
| K-12 Schools (NCES CCD) | 98,957 |
| States Covered | All 50 US States |
| Education Levels | 7 (Preschool → Medical School) |
| Live APIs | 3 (Groq, Tavily, College Scorecard) |
| County Coverage | 96% via ZIP mapping |

---

## 🎯 Features

- **Smart Geographic Filter** — Level → State → District/ISD → City cascade
- **Metro Area Search** — Select Dallas, get UTD (Richardson) and all suburbs
- **Programs Offered** — Engineering, Medicine, Law, Business chips on cards
- **Public First** — Public schools always shown before private
- **District/ISD Filter** — Search by FRISCO ISD, Plano ISD, McKinney ISD etc.
- **PDF Checklists** — Personalized application checklists with AI pro tips
- **ChromaDB Cache** — Repeat queries served instantly from vector cache

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend UI | Streamlit 1.35 |
| LLM Engine | Groq LLaMA 3.3 70B |
| Vector Database | ChromaDB 0.5.3 |
| Embeddings | ChromaDB Default (ONNX) |
| Web Search | Tavily API 0.7.23 |
| PDF Generation | FPDF2 2.7.9 |
| University Data | College Scorecard API |
| K-12 Data | NCES CCD 2022-23 |
| Data Processing | Pandas |
| Runtime | Python 3.11 |

---

## 📁 Project Structure

```
EduNavigatorAI/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── packages.txt                    # System packages
├── .python-version                 # Forces Python 3.11
├── .streamlit/
│   └── config.toml                 # Theme configuration
├── data/
│   ├── schools.csv                 # 50 curated seed schools
│   ├── k12_schools.csv             # 98,957 NCES schools
│   └── zip_county.csv              # ZIP to county mapping
├── agents/
│   ├── orchestrator.py             # Master controller
│   ├── librarian_agent.py          # RAG semantic search
│   ├── researcher_agent.py         # Tavily web search
│   └── doc_specialist_agent.py     # PDF checklist generator
└── utils/
    ├── embeddings.py               # ChromaDB vector store
    ├── geo_filter.py               # Geographic filtering
    ├── nces_api.py                 # K-12 local DB + fallback
    ├── college_scorecard_api.py    # University/Medical API
    ├── build_k12_database.py       # NCES CSV processor
    └── startup.py                  # Startup data checks
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11
- Free API keys for Groq, Tavily, College Scorecard

### Installation

```bash
# Clone the repo
git clone https://github.com/vlh62627/EduNavigatorAI.git
cd EduNavigatorAI

# Create virtual environment
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root folder:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
COLLEGE_SCORECARD_API_KEY=your_college_scorecard_api_key

GROQ_MODEL=llama-3.3-70b-versatile
EMBED_MODEL=all-MiniLM-L6-v2
CHROMA_DB_PATH=./chroma_db
OUTPUT_PATH=./outputs
ANONYMIZED_TELEMETRY=False
```

**Get free API keys:**
- Groq: https://console.groq.com
- Tavily: https://app.tavily.com
- College Scorecard: https://api.data.gov/signup

### Run the App

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 📥 K-12 Database Setup (Optional)

The `data/k12_schools.csv` file is included in the repo (25MB).
To rebuild it from the latest NCES data:

```bash
# Download from https://nces.ed.gov/ccd/files.asp
# Save as data/nces_schools.csv

python utils/build_k12_database.py
```

---

## 🌍 How to Use

1. **Select Education Level** — Preschool, Elementary, Middle, High School, Community College, University, or Medical School
2. **Select State** — All 50 US states available
3. **Select District/City** — K-12 shows District/ISD; University shows City
4. **Click Search** — AI agents find matching schools instantly
5. **Download PDF** — Toggle PDF Checklist and enter school name for a personalized application guide

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 👨‍💻 Author

**Vijay Kumar Panguluri**
Capstone Project — April 2026

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/vijay-panguluri)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/vlh62627)

---

## 📄 License

This project is licensed under the MIT License.

---

*Built with ❤️ using Python, Streamlit, Groq, ChromaDB, Tavily, NCES CCD, and College Scorecard API*
