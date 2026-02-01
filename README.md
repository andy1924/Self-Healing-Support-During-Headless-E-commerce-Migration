# Agentic AI System for Self-Healing Support Operations

This repository implements an **agentic AI system** for managing support operations during a hosted-to-headless SaaS migration.  
The system continuously observes operational signals, reasons about emerging incidents, proposes mitigations, and keeps humans in the decision loop.

The focus is on **autonomy with control**, not instruction-following automation.

---

## System Objective

- Detect emerging support incidents before escalation
- Perform context-aware root cause reasoning
- Propose actions with explicit confidence and risk assessment
- Minimize cascading merchant impact during migration
- Maintain explainability, auditability, and human oversight

---

## Agent Loop

The system follows a closed-loop agentic workflow:

- **Observe**  
  Ingests support tickets and operational signals

- **Reason**  
  Uses LLM-based structured reasoning to form root-cause hypotheses

- **Decide**  
  Generates action plans with uncertainty, confidence, and risk classification

- **Act (Human-in-the-loop)**  
  Executes only human-approved support and communication actions

- **Feedback**  
  Updates system state via ticket lifecycle and audit logs

---

## Architecture Overview


---

## Key Components

- **`dataGenerator.py`**  
  Generates realistic support ticket and merchant activity data.

- **`incidentDetector.py`**  
  Aggregates raw tickets into higher-level incidents using temporal grouping.

- **`decisionAgent.py`**  
  Core agentic reasoning module.  
  Performs LLM-based root cause analysis and produces structured action plans with:
  - Confidence scores
  - Assumptions
  - Uncertainty notes
  - Risk levels  
  All outputs are defensively validated.

- **`uiApp.py`**  
  Human-in-the-loop control plane built with Streamlit.  
  Enables:
  - Incident review
  - Action approval / rejection
  - Ticket lifecycle management
  - Audit log inspection
  - System performance visibility

- **`performanceMonitor.py`**  
  Captures runtime system metrics including:
  - Decision latency
  - CPU utilization
  - Memory usage  
  Metrics are logged for observability and deployment feasibility analysis.

---

## Safety and Control Principles

- No autonomous destructive or irreversible actions
- Explicit human approval required for all interventions
- Confidence, assumptions, and uncertainty surfaced for every decision
- Partial or malformed LLM outputs handled conservatively
- All decisions and communications are logged for auditability

---

## Data Contracts

- Tickets and incidents are treated as **partial and unreliable inputs**
- No component assumes schema completeness
- Missing or inconsistent fields default to conservative interpretations
- All joins between incidents and action plans are performed defensively

---

## Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install streamlit langchain langchain-openai python-dotenv psutil
