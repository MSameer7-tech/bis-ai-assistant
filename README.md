# BIS AI Intelligent Assistant for Indian Standards

An AI-powered conversational assistant for the **Bureau of Indian Standards (BIS)** developed for Smart India Hackathon (SIH).

The assistant enables MSMEs, startups, manufacturers, engineers, consumers, and researchers to navigate Indian Standards, QCOs, certification schemes, testing requirements, and recognized laboratories with trustworthy, source-backed citations.

---

## 📁 Project Structure

```text
bis-ai-assistant/
├── ai/                 # AI pipelines: Ingestion, Chunking, Retrieval, RAG, Reasoning
├── backend/            # FastAPI backend, DB models, API endpoints
├── frontend/           # Web UI (React/Next.js)
├── data/               # Knowledge Base Data
│   ├── raw/            # Original source PDFs and regulatory documents
│   ├── processed/      # Structured machine-readable JSON extracted from documents
│   ├── chunks/         # Structure-aware chunks with metadata
│   └── metadata/       # Source and registry metadata
├── docs/               # Architecture, knowledge maps, API contracts
├── tests/              # Unit, integration, and AI evaluation tests
├── scripts/            # Helper scripts for data processing and evaluation
├── .gitignore
├── .env.example
└── README.md
```

---

## 👥 Team Collaboration Boundaries

- **AI + BIS Knowledge (`ai/`, `data/`, `scripts/`, `tests/`)**:
  - Document acquisition & structure-aware extraction
  - Knowledge representation & metadata modeling
  - Hybrid retrieval & Reranking
  - Rule-based reasoning & Grounded RAG
  - Evaluation & Multilingual processing

- **Backend + Frontend + Platform (`backend/`, `frontend/`)**:
  - FastAPI server & API layer
  - PostgreSQL + pgvector infrastructure
  - User interface, source viewer & interactive chat
  - Deployment & Authentication

---

## 🚀 Getting Started

1. Copy `.env.example` to `.env` and populate necessary API keys and database credentials:
   ```bash
   cp .env.example .env
   ```
2. Set up Python virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
