# AgentLens

## Failure Intelligence for AI-Agent Traces

AgentLens analyzes AI-agent conversations and tool executions to uncover hidden failures that traditional observability tools often miss.

An agent can finish an execution run without throwing exceptions, return HTTP 200s, and report technical success on every tool call—yet still fail the user's task.

**Technical success $\neq$ task success.**

AgentLens evaluates agent behavior against task expectations and tool-execution evidence, isolates concrete evidence, and prioritizes what engineers should investigate first.

---

## What AgentLens Detects

AgentLens identifies five distinct failure patterns:

1. **Unsupported Success (`unsupported_success`)**: The agent claims a task succeeded despite an underlying tool returning an unrecovered failure (e.g., claiming an order was cancelled when the cancellation tool returned "Order already shipped").
2. **Wrong Target (`wrong_target`)**: All tools execute with technical success, but mutate or query a different entity than the one explicitly requested by the user (e.g., user asks to update customer 4821, tool mutates 4890, agent claims customer 4821 was updated).
3. **Incomplete Task (`incomplete_task`)**: The user requests multiple actions, but the agent only executes a subset and claims completion without exercising all required capabilities (e.g., user requests delivery booking and email confirmation, agent books delivery but never calls `send_email`).
4. **Repeated Question (`repeated_question`)**: The agent asks semantically equivalent clarification questions multiple times, indicating lost context or failure to retain previous user answers (measured using `sentence-transformers` semantic similarity).
5. **No Progress (`no_progress`)**: The agent enters an unproductive tool loop, repeatedly issuing the same search or query with zero results and no change in state.

---

## Recovery Safety & Negative Controls

A core design requirement is ensuring that failure detection does not introduce false alarms on legitimate agent behaviors:

- **Legitimate Recoveries**: If a tool times out or fails on an initial attempt but the agent retries and succeeds, AgentLens safely recognizes this as a legitimate recovery rather than an unsupported success.
- **Legitimate Search Refinement**: Successive search queries that return positive results or narrow down symbols/parts are not flagged as no-progress.
- **Honest Failure Disclosures**: If a tool fails and the agent accurately informs the user of the failure or limitation, it is not flagged as an unsupported success.
- **Ambiguous Cases**: Traces with upstream network drops or unconfirmed statuses are handled safely without being misclassified.

---

## Agent and Tool Profiles

AgentLens decouples detector logic from hardcoded domain strings using explicit **Agent Profiles** ([`agentlens/schema/profiles.py`](file:///c:/Users/Lenovo%20Thinkpad%20YOGA/Documents/Experiments/Agentlens/agentlens/schema/profiles.py)):

- **Customer Support Agent** (`customer_support_v1`): Tools for order lookups, cancellations, customer account updates, delivery booking, emails, and inventory search.
- **Coding Agent** (`coding_agent_v1`): Tools for `search_code`, `read_file`, `write_file`, `run_tests`, `git_diff`, and `run_command`.

The same detection engine was evaluated across two synthetic agent domains—customer support and software engineering—using domain-specific agent/tool profiles without requiring an LLM.

---

## Evaluation Benchmark

Evaluated on two controlled synthetic datasets (113 traces total):

### 1. Customer Support Domain (65 traces)
- **Failure Detection**:
  - Precision: **1.00**
  - Recall: **1.00**
  - F1-Score: **1.00**
- **Failure Classification**:
  - `wrong_target`: 7/7 (F1: 1.00)
  - `unsupported_success`: 8/8 (F1: 1.00)
  - `repeated_question`: 7/7 (F1: 1.00)
  - `no_progress`: 6/6 (F1: 1.00)
  - `incomplete_task`: 7/7 (F1: 1.00)
- **Recovery Safety**: 8/8 legitimate recoveries correctly preserved (0 false alarms).
- **Controls**: 4 ambiguous cases + 8 hard negative controls correctly preserved.

### 2. Coding Agent Domain (48 traces)
- **Failure Detection**:
  - Precision: **1.00**
  - Recall: **1.00**
  - F1-Score: **1.00**
- **Failure Classification**:
  - `unsupported_success`: 6/6 (F1: 1.00)
  - `incomplete_task`: 6/6 (F1: 1.00)
  - `no_progress`: 5/5 (F1: 1.00)
  - `repeated_question`: 5/5 (F1: 1.00)
- **Recovery Safety**: 6/6 legitimate recoveries correctly preserved (0 false alarms).
- **Controls**: 4 ambiguous cases + 8 hard negative controls correctly preserved.

*Note: These metrics reflect evaluation on controlled synthetic benchmarks for prototype validation, not claims of real-world production performance.*

---

## Project Structure

```
agentlens/
├── app/
│   └── streamlit_app.py          # Interactive cross-domain dashboard
├── data/
│   ├── traces.json               # Customer support traces (65 traces)
│   ├── ground_truth.json         # Customer support ground truth labels
│   ├── coding_traces.json        # Coding agent traces (48 traces)
│   ├── coding_ground_truth.json  # Coding agent ground truth labels
│   ├── generate_dataset.py       # Customer support generator
│   └── generate_coding_dataset.py# Coding agent generator
├── agentlens/
│   ├── schema/
│   │   ├── models.py             # Event, Task, Trace, Finding models
│   │   └── profiles.py           # Agent and Tool capability profiles
│   ├── detectors/
│   │   └── rules.py              # Rule & semantic similarity detectors
│   ├── analysis/
│   │   ├── pipeline.py           # Analysis pipeline
│   │   ├── prioritization.py     # Investigation priority scoring
│   │   └── similarity.py         # SentenceTransformer similarity
│   └── ingestion/
│       └── loader.py             # Trace dataset loader
├── evaluation/
│   └── evaluate.py               # Multi-domain evaluation suite
├── tests/
│   └── test_detectors.py         # Automated detector regression tests
└── run_analysis.py               # CLI analysis entrypoint
```

---

## Getting Started

### 1. Installation

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e .
```

### 2. Generate Synthetic Datasets

```bash
python data/generate_dataset.py
python data/generate_coding_dataset.py
```

### 3. Run CLI Analysis

```bash
# Analyze both domains
python run_analysis.py

# Or analyze a specific domain
python run_analysis.py customer
python run_analysis.py coding
```

### 4. Run Evaluation Suite

```bash
python evaluation/evaluate.py
```

### 5. Launch the Dashboard

```bash
streamlit run app/streamlit_app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. Use the sidebar to switch between the **Customer Support Agent** and **Coding Agent** domains.

---

## Roadmap

- [x] **V1 — Deterministic Baseline**: 6 traces, 4 initial detectors, CLI analysis, basic dashboard.
- [x] **V2 — Scaled Evaluation**: 50 traces, ground truth generation, semantic similarity via `sentence-transformers`, recovery safety metrics.
- [x] **V2.5 — Robustness & Multi-Domain**: Added `wrong_target`, hard negative controls, realistic task descriptions, coding agent domain, and agent/tool capability profiles.
- [ ] **V3 — Cross-Trace Intelligence**: Trace embeddings, failure clustering, recurring failure pattern discovery, cluster-level investigation prioritization.
- [ ] **V4 — OpenTelemetry & Ingestion**: OpenTelemetry / OpenInference standards, adapters for major agent frameworks (LangGraph, CrewAI, AutoGen).
- [ ] **V5 — LLM-Assisted Ambiguity Analysis**: Targeted LLM evaluation reserved strictly for ambiguous traces.