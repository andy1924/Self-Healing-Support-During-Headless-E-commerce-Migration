# Agentic AI System for Self-Healing Support Operations

This repository implements an **agentic AI system** designed to manage support operations during a hosted-to-headless SaaS migration. The system observes operational signals, reasons about incident causes, proposes mitigations, and keeps humans in the decision loop.

The implementation emphasizes **autonomy with control**, not instruction-following automation.

---

## System Objective

- Detect emerging support incidents early
- Perform context-aware root cause reasoning
- Propose actions with confidence and risk assessment
- Prevent cascading merchant impact
- Maintain explainability and human oversight

---

## Agent Loop


- **Observe:** Support tickets, incident aggregates
- **Reason:** LLM-based hypothesis generation over structured signals
- **Decide:** Action planning with uncertainty and risk classification
- **Act:** Human-approved execution (support, communication)
- **Feedback:** State updates via ticket lifecycle

---

## Architecture Overview


---

## Key Components

- `dataGenerator.py`  
  Generates realistic support ticket data.

- `incidentDetector.py`  
  Aggregates tickets into incidents using temporal and semantic grouping.

- `decisionAgent.py`  
  Performs LLM-based reasoning to infer root causes and propose actions.  
  Outputs structured, defensively-validated JSON.

- `uiApp.py`  
  Human-in-the-loop control plane for inspection, approval, and execution.

---

## Safety and Control

- No autonomous destructive actions
- Explicit human approval for all interventions
- Confidence, assumptions, and uncertainty surfaced
- Invalid or partial LLM outputs handled safely
- All communications and decisions logged

---

## Data Contracts

- Tickets and incidents are treated as **partial and unreliable inputs**
- UI and agents never assume schema completeness
- Missing fields default to conservative interpretations

---

## Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install streamlit langchain langchain-openai python-dotenv
```
---
## API Key

OPENAI_API_KEY = your_key_here

