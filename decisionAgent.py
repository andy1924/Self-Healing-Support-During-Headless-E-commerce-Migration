"""
decisionAgent.py
LLM-based decision agent that reasons over detected incidents
and proposes support, engineering, or documentation actions.
"""

# ---------------------------------------------------
# Imports
# ---------------------------------------------------

import json
import time
from typing import List, Dict
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# --- OPTIONAL PERFORMANCE IMPORTS (SAFE) ---
try:
    import psutil
except ImportError:
    psutil = None

# ---------------------------------------------------
# Environment Setup
# ---------------------------------------------------

load_dotenv()

# ---------------------------------------------------
# LLM Initialization - Directly Takes API key from .env
# ---------------------------------------------------

llm = ChatOpenAI(model="gpt-4o-mini")

# ---------------------------------------------------
# File Paths
# ---------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INCIDENTS_FILE_PATH = os.path.join(BASE_DIR, "data", "incidents.json")
OUTPUT_FILE_PATH = os.path.join(BASE_DIR, "actionPlans.json")

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------

def loadIncidents() -> List[Dict]:
    """Load detected incidents from JSON file."""
    with open(INCIDENTS_FILE_PATH, "r") as file:
        return json.load(file)


def buildReasoningPrompt(incident: Dict) -> List:
    """
    Handles partial incident data safely.
    """

    from datetime import datetime

    firstSeen = datetime.fromisoformat(incident["firstSeen"])
    lastUpdated = datetime.fromisoformat(incident["lastUpdated"])
    timeWindowMinutes = int((lastUpdated - firstSeen).total_seconds() / 60)

    systemPrompt = """
        You are an autonomous support operations agent for a SaaS platform
        migrating from hosted to headless architecture.
        
        Some incident data may be incomplete or missing.
        Reason conservatively and surface uncertainty.
        
        Your task:
        1. Diagnose the most likely root cause of the incident
        2. Propose an action plan with confidence level
        3. Clearly state assumptions and uncertainty
        4. Respect safety boundaries (no destructive actions)
        
        Respond ONLY in valid JSON.
        """

    humanPrompt = f"""
        Incident details:
        - Incident ID: {incident["incidentId"]}
        - Issue Type: {incident["issueType"]}
        - Ticket Count: {incident["ticketCount"]}
        - Affected Merchants: {incident["affectedMerchants"]}
        - Time Window (minutes): {timeWindowMinutes}
        - Incident Status: {incident["status"]}
        
        Return JSON with the following structure:
        {{
          "incidentId": "{incident["incidentId"]}",
          "rootCauseHypothesis": "...",
          "confidenceLevel": 0.0-1.0,
          "recommendedActions": [
            {{
              "actionType": "support | engineering | documentation | mitigation",
              "description": "...",
              "requiresHumanApproval": true/false,
              "riskLevel": "low | medium | high"
            }}
          ],
          "assumptions": ["..."],
          "uncertaintyNotes": "..."
        }}
        """

    return [
        SystemMessage(content=systemPrompt),
        HumanMessage(content=humanPrompt)
    ]


def reasonAboutIncident(incident: Dict) -> Dict:
    """Invoke LLM to reason about a single incident."""

    # -------------------------------
    # Performance Measurement (START)
    # -------------------------------

    startTime = time.time()

    if psutil:
        process = psutil.Process()
        cpuBefore = process.cpu_times()
        memBeforeMB = process.memory_info().rss / (1024 ** 2)
    else:
        cpuBefore = None
        memBeforeMB = None

    # -------------------------------
    # Existing Logic (UNCHANGED)
    # -------------------------------

    messages = buildReasoningPrompt(incident)
    response = llm.invoke(messages)

    try:
        decision = json.loads(response.content)
    except json.JSONDecodeError:
        decision = {
            "incidentId": incident["incidentId"],
            "error": "LLM returned invalid JSON",
            "rawResponse": response.content
        }

    # -------------------------------
    # Performance Measurement (END)
    # -------------------------------

    endTime = time.time()
    latencySeconds = round(endTime - startTime, 3)

    if psutil and cpuBefore:
        cpuAfter = process.cpu_times()
        memAfterMB = process.memory_info().rss / (1024 ** 2)

        cpuDeltaSeconds = round(
            (cpuAfter.user + cpuAfter.system) -
            (cpuBefore.user + cpuBefore.system),
            3
        )

        memoryDeltaMB = round(memAfterMB - memBeforeMB, 2)
    else:
        cpuDeltaSeconds = None
        memoryDeltaMB = None

    # -------------------------------
    # Attach Metrics (NON-DESTRUCTIVE)
    # -------------------------------

    decision["performanceMetrics"] = {
        "latencySeconds": latencySeconds,
        "cpuTimeSeconds": cpuDeltaSeconds,
        "memoryDeltaMB": memoryDeltaMB,
        "profilingNote": "Local CPU/RAM only. LLM inference executed remotely."
    }

    return decision


# ---------------------------------------------------
# Main Agent Loop
# ---------------------------------------------------

def runDecisionAgent():
    """
    Main observe → reason → decide loop.
    Acts on incidents, not raw tickets.
    """

    incidents = loadIncidents()
    actionPlans = []

    for incident in incidents:
        print(f"Reasoning about incident {incident['incidentId']}...")
        decision = reasonAboutIncident(incident)
        actionPlans.append(decision)

    with open(OUTPUT_FILE_PATH, "w") as file:
        json.dump(actionPlans, file, indent=2)

    print(f"Decision agent completed. {len(actionPlans)} action plans generated.")


# ---------------------------------------------------
# Entry Point
# ---------------------------------------------------

if __name__ == "__main__":
    runDecisionAgent()
