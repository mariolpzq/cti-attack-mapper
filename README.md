# CTI ATT&CK Mapper

An LLM agent that extracts MITRE ATT&CK techniques from cyber threat intelligence (CTI) reports, using LangChain for agent orchestration and RAG over the MITRE ATT&CK Enterprise knowledge base.

## What it does

Given a CTI report (e.g., a Mandiant blog post or CISA advisory), the agent:

1. Reads the narrative prose describing adversary behavior.
2. For each candidate behavior, queries a vector store of ATT&CK techniques via RAG.
3. Decides which retrieved technique (if any) actually matches the described behavior.
4. Returns a structured JSON list of techniques with supporting evidence quotes.

The output is evaluated against ground-truth ATT&CK mappings published alongside real CTI reports.

## Architecture

```
CTI report (text)
      │
      ▼
┌─────────────────────┐      ┌──────────────────────┐
│  Extraction Agent   │◄────►│  ATT&CK Vector Store │
│  (LangChain+Gemini) │      │  (Chroma + MiniLM)   │
└─────────┬───────────┘      └──────────────────────┘
          │
          ▼
   Structured JSON
   - techniques[]
   - evidence quotes
          │
          ▼
   Eval harness
   (precision/recall/F1
    vs ground truth)
```

## Setup

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set your Gemini API key (free tier at https://aistudio.google.com)
cp .env.example .env
# edit .env and add GOOGLE_API_KEY=your_key_here
```

## How to run

### 1. Build the ATT&CK vector store (run once)

```bash
uv run python -m src.attack_loader
```

This downloads the Enterprise ATT&CK STIX bundle, embeds each technique's description with `sentence-transformers/all-MiniLM-L6-v2`, and stores it in a local Chroma DB at `./data/chroma`.

### 2. Extract techniques from a single report

```bash
uv run python -m src.extractor eval/reports/report_1.txt
```

Outputs structured JSON to stdout.

### 3. Run the full eval

```bash
uv run python -m eval.run_eval
```

Runs the agent on every `report_N.txt` in `eval/reports/`, compares against `report_N_truth.json`, and prints per-report and macro-averaged precision/recall/F1.

Results are also written to `eval/results.md`.

## Repo layout

```
cti-attack-mapper/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── attack_loader.py    # Download STIX → embed → Chroma
│   ├── tools.py            # search_attack_techniques tool
│   ├── agent.py            # LangChain agent setup
│   └── extractor.py        # Top-level CLI
├── eval/
│   ├── __init__.py
│   ├── run_eval.py         # Eval harness
│   ├── reports/            # report_N.txt + report_N_truth.json
│   └── results.md          # Eval writeup (filled in after running)
└── data/
    └── chroma/             # Local vector store (gitignored)
```

## Results

See `eval/results.md` after running the eval.

## Limitations

- Single LLM backend tested (Gemini 1.5 Flash).
- Reports truncated to first 8000 tokens; no chunking for very long reports.
- Strict T-ID matching only (no parent-technique partial credit).
- No fine-tuning; relies on prompt + retrieval alone.
- Small eval set (5 reports).

## What I'd do next

- Add a self-critique step where the agent reviews its own output before returning.
- Compare against open-weight models (e.g., Llama 3) for cost/quality tradeoffs.
- Expand eval set to 20+ reports and add adversarial cases (e.g., reports with no real techniques).
- Add lenient parent-technique scoring alongside strict.
- Chunk long reports and aggregate technique sets across chunks.
