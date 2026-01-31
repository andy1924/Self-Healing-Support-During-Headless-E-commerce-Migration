"""
decisionAgent.py

LLM-based agent that analyzes detected incidents
and proposes support, engineering, or documentation actions.
"""
#hi
import json
from typing import List, Dict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


# Load environment variables (API keys)ssss
load_dotenv()


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")


# File paths
INCIDENTS_FILE_PATH = "D:\\PythonProject\\CC_Hackathon_B108\\data\\incidents.json"
OUTPUT_FILE_PATH = "actionPlans.json"


def loadIncidents() -> List[Dict]:
    """Load detected incidents from file."""
    with open(INCIDENTS_FILE_PATH, "r") as file:
        return json.load(file)


def buildReasoningPrompt(incident: Dict) -> List:
    """
    Build a structured prompt for the LLM.
    Handles missing or partial incident data safely.
    """
    from datetime import datetime

    firstSeen = datetime.fromisoformat(incident["firstSeen"])
    lastUpdated = datetime.fromisoformat(incident["lastUpdated"])
    timeWindowMinutes = int((lastUpdated - firstSeen).total_seconds() / 60)

    systemPrompt = """
You are an autonomous support operations agent for a SaaS platform
migrating from hosted to headless architecture.

Some incident data may be incomplete.
Reason conservatively and surface uncertainty.

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

Return JSON in this format:
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
    """Run LLM reasoning for a single incident."""
    messages = buildReasoningPrompt(incident)
    response = llm.invoke(messages)

    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "incidentId": incident["incidentId"],
            "error": "Invalid JSON returned by LLM",
            "rawResponse": response.content
        }


def runDecisionAgent():
    """
    Main agent loop:
    observe incidents → reason → produce action plans
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


if __name__ == "__main__":
    runDecisionAgent()
