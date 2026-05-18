# CTI ATT&CK Mapper (WIP)

An LLM agent that extracts MITRE ATT&CK techniques from cyber threat intelligence (CTI) reports using LangChain for agent orchestration and RAG over the MITRE ATT&CK Enterprise knowledge base.

## How it works

```
CTI report (text)
      │
      ▼
┌─────────────────────┐      ┌──────────────────────┐
│  Extraction Agent   │◄────►│  ATT&CK Vector Store │
│  (LangChain+Groq)   │      │  (FAISS + MiniLM)    │
└─────────┬───────────┘      └──────────────────────┘
          │
          ▼
   Structured JSON
   { techniques[], evidence quotes }
          │
          ▼
   Eval harness
   precision / recall / F1
   vs published ground truth
```

Given a CTI report, the agent identifies discrete adversary behaviors, queries the ATT&CK vector store for each via RAG, and returns a structured JSON list of matched techniques with supporting evidence quotes from the source text.

## Setup

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Configure API keys
# edit .env — set GROQ_API_KEY 
# optionally set HF_TOKEN

# 4. Build the ATT&CK vector store
uv run python -m src.attack_loader
```

## Usage

**Extract techniques from a single report:**
```bash
uv run python -m src.agent eval/reports/report_1.txt
```

**Run the full eval across all reports:**
```bash
uv run python -m eval.run_eval
```

Results are printed to stdout and written to `eval/results.md`.

## Repo layout

```
cti-attack-mapper/
├── src/
│   ├── attack_loader.py   # Download ATT&CK STIX → embed → FAISS
│   ├── tools.py           # search_attack_techniques RAG tool
│   └── agent.py           # LangChain agent + extract_techniques()
├── eval/
│   ├── run_eval.py        # Eval harness (precision/recall/F1)
│   ├── reports/           # report_N.txt + report_N_truth.json
│   └── results.md         # Results and error analysis
└── pyproject.toml
```

## Results

See `eval/results.md`.

## Limitations

- No fine-tuning; relies entirely on prompt + RAG retrieval.
- Reports truncated to around 8k tokens.
- Strict T-ID exact match only.
- Eval set is small (3 reports).

---

## Related work

This project sits in a line of research on automating ATT&CK extraction from CTI text. Key references:

**TRAM (Threat Report ATT&CK Mapper)** — MITRE Engenuity / Center for Threat-Informed Defense  
The canonical baseline for this task. Originally fine-tuned SciBERT on 11,300 annotated CTI sentences covering the 50 most common ATT&CK techniques. Later updated to use fine-tuned LLMs. A key limitation: annotation effort constrained coverage to 50 of ~600+ techniques.  
→ [GitHub](https://github.com/center-for-threat-informed-defense/tram) · [CTID project page](https://ctid.mitre.org/projects/threat-report-attck-mapper-tram/)

**"Towards Effective Identification of Attack Techniques in CTI Reports using LLMs"** (arXiv 2505.03147, 2025)  
Benchmarks zero-shot Llama2 variants against TRAM (SciBERT) on two annotated datasets, with and without LLM-based report summarisation as a preprocessing step. Reports F1 scores for each configuration — directly comparable to this project's approach.  
→ [arXiv:2505.03147](https://arxiv.org/abs/2505.03147)

**"Instantiating Standards: Enabling Standard-Driven TTP Extraction with Evolvable Memory"** (arXiv 2505.09261, 2025)  
Proposes converting ATT&CK standard definitions into a dual-layer "evolvable memory" that an LLM can query and update. Highlights exactly the retrieval ambiguity problem this project faces: hundreds of techniques with overlapping descriptions make RAG-based disambiguation hard.  
→ [arXiv:2505.09261](https://arxiv.org/abs/2505.09261)

**"LLMCloudHunter"** (arXiv 2407.05194, 2024)  
LLM pipeline for extracting TTPs, IoCs, and API calls from cloud-focused OSCTI, achieving 80%/83% precision/recall. Uses STIX-formatted ATT&CK data as the knowledge source — same design choice as this project.  
→ [arXiv:2407.05194](https://arxiv.org/abs/2407.05194)

**"Security Logs to ATT&CK Insights: LLMs for Threat Understanding"** (arXiv 2510.20930, 2024)  
Applies LLMs to IDS logs rather than prose CTI reports — mapping behavioral phases to ATT&CK techniques from telemetry. Relevant because the same RAG-over-ATT&CK design applies to structured log data, the direction this project could extend toward.  
→ [arXiv:2510.20930](https://arxiv.org/abs/2510.20930)

**"MITRE ATT&CK Applications in Cybersecurity and The Way Forward"** (arXiv 2502.10825, 2025)  
Survey of the full landscape of ATT&CK-based research, covering TTP extraction, malware detection, APT attribution, and SOC integration. Good map of where this project fits in the broader literature.  
→ [arXiv:2502.10825](https://arxiv.org/abs/2502.10825)