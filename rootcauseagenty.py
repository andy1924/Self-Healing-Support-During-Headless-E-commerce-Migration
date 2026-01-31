import json
from pathlib import Path
from collections import Counter

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------

dataDir = Path("data")

incidentsFile = dataDir / "incidents.json"
merchantStateFile = dataDir / "merchantMigrationState.json"
errorMetricsFile = dataDir / "errorMetrics.json"
knownIssuesFile = dataDir / "knownIssues.json"

analysisOutputFile = dataDir / "incidentAnalysis.json"

# ---------------------------------------------------
# Load Data Sources
# ---------------------------------------------------

with open(incidentsFile, "r") as file:
    incidents = json.load(file)

with open(merchantStateFile, "r") as file:
    merchantStates = {m["merchantId"]: m for m in json.load(file)}

with open(errorMetricsFile, "r") as file:
    errorMetrics = json.load(file)

with open(knownIssuesFile, "r") as file:
    knownIssues = json.load(file)

# ---------------------------------------------------
# Helper Functions
# ---------------------------------------------------

def findMerchantPatterns(merchantIds):
    """Extract common migration and configuration patterns"""
    patterns = Counter()

    for merchantId in merchantIds:
        state = merchantStates.get(merchantId)
        if not state:
            continue

        if state["frontendVersion"] == "v2" and state["backendVersion"] == "v1":
            patterns["frontendBackendMismatch"] += 1

        if not state["webhooksConfigured"]:
            patterns["missingWebhooks"] += 1

        if not state["apiKeyValid"]:
            patterns["invalidApiKey"] += 1

        patterns[f"migrationStage_{state['migrationStage']}"] += 1

    return patterns


def findRelevantErrors(issueType):
    """Map issue types to relevant platform services"""
    serviceMap = {
        "checkoutFailure": "checkoutApi",
        "apiError": "authApi",
        "webhookMissing": "webhookService"
    }

    targetService = serviceMap.get(issueType)
    if not targetService:
        return []

    return [
        metric for metric in errorMetrics
        if metric["service"] == targetService
    ]


# ---------------------------------------------------
# Root Cause Reasoning
# ---------------------------------------------------

incidentAnalyses = []

for incident in incidents:
    merchantIds = incident["affectedMerchants"]
    merchantPatterns = findMerchantPatterns(merchantIds)
    relatedErrors = findRelevantErrors(incident["issueType"])

    hypothesis = "unknown"
    confidence = 0.3
    evidence = []
    uncertainties = []

    # ---- Hypothesis 1: Frontend / Backend Version Mismatch ----
    if merchantPatterns.get("frontendBackendMismatch", 0) >= 2:
        hypothesis = "frontendBackendVersionMismatch"
        confidence = 0.75
        evidence.append("Multiple merchants have frontend v2 with backend v1")
        uncertainties.append("Backend logs do not explicitly confirm mismatch")

    # ---- Hypothesis 2: Merchant Configuration Error ----
    elif merchantPatterns.get("missingWebhooks", 0) >= 2:
        hypothesis = "merchantWebhookMisconfiguration"
        confidence = 0.7
        evidence.append("Webhooks not configured for affected merchants")
        uncertainties.append("Some merchants report intermittent success")

    # ---- Hypothesis 3: Platform Regression ----
    elif relatedErrors and relatedErrors[0]["countLast15Min"] > 30:
        hypothesis = "platformServiceDegradation"
        confidence = 0.8
        evidence.append("High error rate detected in platform service")
        uncertainties.append("No recent deployment data available")

    else:
        uncertainties.append("Insufficient evidence for a strong hypothesis")

    incidentAnalyses.append({
        "incidentId": incident["incidentId"],
        "issueType": incident["issueType"],
        "hypothesis": hypothesis,
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "uncertainties": uncertainties,
        "merchantPatternSummary": dict(merchantPatterns)
    })

# ---------------------------------------------------
# Save Analysis Results
# ---------------------------------------------------

with open(analysisOutputFile, "w") as file:
    json.dump(incidentAnalyses, file, indent=2)

print(f"Root cause analysis complete. {len(incidentAnalyses)} incidents analyzed.")
