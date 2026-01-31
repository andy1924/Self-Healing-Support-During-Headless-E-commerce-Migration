import json
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

# Time window (in minutes) to group tickets into one incident
incidentWindowMinutes = 30

dataDir = Path("data")

ticketsFile = dataDir / "supportTickets.json"
incidentsFile = dataDir / "incidents.json"

# ---------------------------------------------------
# Utility Functions
# ---------------------------------------------------

def parseTimestamp(timestampStr):
    """Parse ISO timestamp string into datetime object"""
    return datetime.fromisoformat(timestampStr)


def isWithinWindow(baseTime, compareTime, windowMinutes):
    """Check if two timestamps fall within the incident window"""
    return abs((compareTime - baseTime).total_seconds()) <= windowMinutes * 60


# ---------------------------------------------------
# Incident Detection Logic
# ---------------------------------------------------

# Load support tickets
with open(ticketsFile, "r") as file:
    supportTickets = json.load(file)

# Sort tickets chronologically for deterministic grouping
supportTickets.sort(key=lambda t: t["timestamp"])

incidents = []
incidentCounter = 1

for ticket in supportTickets:
    ticketTime = parseTimestamp(ticket["timestamp"])
    matchedIncident = None

    # Try to associate ticket with an existing open incident
    for incident in incidents:
        incidentTime = parseTimestamp(incident["firstSeen"])

        if (
            incident["issueType"] == ticket["issueType"]
            and isWithinWindow(incidentTime, ticketTime, incidentWindowMinutes)
        ):
            matchedIncident = incident
            break

    if matchedIncident:
        # Add ticket to existing incident
        matchedIncident["ticketIds"].append(ticket["ticketId"])
        matchedIncident["affectedMerchants"].add(ticket["merchantId"])
        matchedIncident["lastUpdated"] = ticket["timestamp"]
        matchedIncident["ticketCount"] += 1
    else:
        # Create a new incident
        newIncident = {
            "incidentId": f"INC-{incidentCounter:03}",
            "issueType": ticket["issueType"],
            "ticketIds": [ticket["ticketId"]],
            "affectedMerchants": {ticket["merchantId"]},
            "ticketCount": 1,
            "firstSeen": ticket["timestamp"],
            "lastUpdated": ticket["timestamp"],
            "status": "open"
        }

        incidents.append(newIncident)
        incidentCounter += 1

# Convert merchant sets to lists for JSON serialization
for incident in incidents:
    incident["affectedMerchants"] = list(incident["affectedMerchants"])

# Save detected incidents
with open(incidentsFile, "w") as file:
    json.dump(incidents, file, indent=2)

print(f"Incident detection complete. {len(incidents)} incidents saved.")
