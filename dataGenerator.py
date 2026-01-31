#Do Not Run this file again and gain id /data exits.
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

# Number of merchants to simulate in the system
numMerchants = 50

# Number of support tickets to generate
numTickets = 120

# Output directory for generated data
dataDir = Path("data")
dataDir.mkdir(exist_ok=True)

# Seed randomness for reproducibility during demos
random.seed(42)


print("Generating Data..........")
# ---------------------------------------------------
# Merchant Migration State
# ---------------------------------------------------
# This dataset represents the current migration context
# for each merchant. It is critical for root-cause reasoning.

merchantMigrationState = []

for i in range(1, numMerchants + 1):
    frontendVersion = random.choice(["v1", "v2"])
    backendVersion = random.choice(["v1", "v2"])

    merchantMigrationState.append({
        "merchantId": f"M-{i:03}",
        "migrationStage": random.choice(["pre", "mid", "post"]),
        "frontendVersion": frontendVersion,
        "backendVersion": backendVersion,
        "webhooksConfigured": random.choice([True, False]),
        "apiKeyValid": random.choice([True, False])
    })

with open(dataDir / "merchantMigrationState.json", "w") as file:
    json.dump(merchantMigrationState, file, indent=2)

# ---------------------------------------------------
# Support Tickets
# ---------------------------------------------------
# This dataset simulates inbound merchant issues.
# Tickets are intentionally repetitive to enable pattern detection.

issueTemplates = [
    ("checkoutFailure", "Checkout returns 500 after frontend upgrade"),
    ("apiError", "API authentication failing intermittently"),
    ("webhookMissing", "Order webhooks not triggering"),
    ("configError", "Integration broke after migration"),
    ("latencyIssue", "Checkout loading very slowly")
]

supportTickets = []
startTime = datetime.now() - timedelta(hours=6)

for i in range(numTickets):
    merchant = random.choice(merchantMigrationState)
    issueType, description = random.choice(issueTemplates)

    supportTickets.append({
        "ticketId": f"TCK-{1000 + i}",
        "merchantId": merchant["merchantId"],
        "issueType": issueType,
        "description": description,
        "timestamp": (
            startTime + timedelta(minutes=random.randint(1, 360))
        ).isoformat(),
        "channel": random.choice(["email", "chat", "dashboard"])
    })

with open(dataDir / "supportTickets.json", "w") as file:
    json.dump(supportTickets, file, indent=2)

# ---------------------------------------------------
# Platform Error Metrics (Aggregated)
# ---------------------------------------------------
# These metrics represent proactive system-level signals.
# The agent uses these to detect incidents before tickets spike.

services = ["checkoutApi", "authApi", "webhookService"]
errorMetrics = []

for service in services:
    errorMetrics.append({
        "service": service,
        "errorCode": random.choice([400, 401, 403, 500]),
        "countLast15Min": random.randint(5, 60),
        "merchantsAffected": random.randint(3, 25),
        "timestamp": datetime.now().isoformat()
    })

with open(dataDir / "errorMetrics.json", "w") as file:
    json.dump(errorMetrics, file, indent=2)

# ---------------------------------------------------
# Known Issues (Seed Memory)
# ---------------------------------------------------
# This dataset represents historical knowledge.
# It allows the agent to demonstrate learning and recall.

knownIssues = [
    {
        "knownIssueId": "KI-001",
        "pattern": "frontendV2 + backendV1",
        "impact": "checkoutFailure",
        "rootCause": "versionMismatch",
        "recommendedAction": "delayFrontendRollout"
    },
    {
        "knownIssueId": "KI-002",
        "pattern": "webhooksConfigured=false",
        "impact": "orderEventsMissing",
        "rootCause": "merchantConfigError",
        "recommendedAction": "guideWebhookSetup"
    }
]

with open(dataDir / "knownIssues.json", "w") as file:
    json.dump(knownIssues, file, indent=2)

print("Data generation complete. Files saved to /data")
