import json
import streamlit as st
import os
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict

# ---------------------------------------------------
# 1. CONFIG & STYLE
# ---------------------------------------------------
st.set_page_config(page_title="Support Ops Control Plane", layout="wide")

st.markdown("""
    <style>
    /* Dark Mode Theme */
    [data-testid="stAppViewContainer"] { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stHeader"] { background-color: #0E1117; }
    h1, h2, h3, h4, h5, h6, p, li, label, div { color: #E0E0E0 !important; font-family: 'Segoe UI', sans-serif; }

    /* Action Cards */
    .action-card {
        background-color: #1E1E1E; border: 1px solid #303030;
        padding: 20px; border-radius: 10px; margin-bottom: 15px;
    }
    .card-header { color: #FF5252 !important; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }

    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #262730; color: #FFFFFF; border: 1px solid #4A4A4A;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# 2. DYNAMIC PATHS (The Fix)
# ---------------------------------------------------
# This finds the folder where uiApp.py is currently sitting
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Construct paths relative to the script location
INCIDENTS_FILE = os.path.join(DATA_DIR, "incidents.json")
TICKETS_FILE = os.path.join(DATA_DIR, "supportTickets.json")
ACTION_PLANS_FILE = os.path.join(BASE_DIR, "actionPlans.json")  # In Root
EMAIL_OUTBOX_FILE = os.path.join(DATA_DIR, "emailOutbox.json")  # In Data
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "auditLog.json")  # In Data


# ---------------------------------------------------
# 3. ROBUST DATA HELPERS
# ---------------------------------------------------
def load_data(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_data(path: str, data: List[Dict]):
    """Creates the folder and saves the file."""
    # Ensure the folder exists (e.g., 'data')
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def clean_id(val):
    if val is None: return ""
    return str(val).strip().lower()


def build_plan_lookup(plans: List[Dict]) -> Dict:
    lookup = {}
    for p in plans:
        raw_id = p.get("incidentId") or p.get("incident_id") or p.get("id")
        if raw_id:
            std_id = clean_id(raw_id)
            lookup[std_id] = p
            numeric = re.sub(r'\D', '', std_id)
            if numeric:
                lookup[numeric] = p
                lookup[str(int(numeric))] = p
    return lookup


def find_plan(incident_id: str, lookup: Dict) -> Dict:
    iid = clean_id(incident_id)
    if iid in lookup: return lookup[iid]
    numeric = re.sub(r'\D', '', iid)
    if numeric:
        if numeric in lookup: return lookup[numeric]
        try:
            if str(int(numeric)) in lookup: return lookup[str(int(numeric))]
        except:
            pass
    return {}


def log_decision(iid, decision, notes):
    """Loads audit log, adds new entry, and saves it."""
    log = load_data(AUDIT_LOG_FILE)
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "incident_id": iid,
        "decision": decision,
        "notes": notes
    }
    log.insert(0, entry)
    save_data(AUDIT_LOG_FILE, log)


# ---------------------------------------------------
# 4. INITIALIZATION
# ---------------------------------------------------
if "page" not in st.session_state: st.session_state.page = "dashboard"
if "incident_idx" not in st.session_state: st.session_state.incident_idx = 0

incidents = load_data(INCIDENTS_FILE)
tickets = load_data(TICKETS_FILE)
actionPlans = load_data(ACTION_PLANS_FILE)
plansByIncident = build_plan_lookup(actionPlans)

# ---------------------------------------------------
# 5. SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.title("🛡️ Support Ops")
    st.caption("Status: **Online**")
    st.markdown("---")

    if st.button("📊 Dashboard", use_container_width=True): st.session_state.page = "dashboard"
    if st.button("🚨 Incident Queue", use_container_width=True): st.session_state.page = "incidents"
    if st.button("🎫 Ticket Desk", use_container_width=True): st.session_state.page = "tickets"
    if st.button("📜 Audit Log", use_container_width=True): st.session_state.page = "audit"

    st.markdown("---")
    with st.expander("🛠 System Paths (Debug)"):
        st.write(f"**Root:** `{BASE_DIR}`")
        st.write(f"**Data:** `{DATA_DIR}`")
        st.write(f"**Audit File:** `{AUDIT_LOG_FILE}`")

# ---------------------------------------------------
# PAGE: DASHBOARD
# ---------------------------------------------------
if st.session_state.page == "dashboard":
    st.title("Operations Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Incidents", len(incidents))
    c2.metric("Open Tickets", len([t for t in tickets if t.get("status", "open") == "open"]))
    c3.metric("Action Plans", len(actionPlans))

# ---------------------------------------------------
# PAGE: INCIDENTS
# ---------------------------------------------------
elif st.session_state.page == "incidents":
    if not incidents:
        st.info("No incidents found.")
    elif st.session_state.incident_idx >= len(incidents):
        st.success("🎉 All incidents reviewed!")
        if st.button("Reset Queue"):
            st.session_state.incident_idx = 0
            st.rerun()
    else:
        curr = incidents[st.session_state.incident_idx]
        iid_raw = curr.get("incidentId") or curr.get("id") or "Unknown"
        plan = find_plan(iid_raw, plansByIncident)

        st.title(f"Reviewing: {iid_raw}")
        st.progress((st.session_state.incident_idx + 1) / len(incidents))

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Incident Profile")
            st.info(f"**Issue:** {curr.get('issueType', 'N/A')}\n\n**Status:** {curr.get('status', 'N/A')}")
            st.write(f"**Impact:** {len(curr.get('affectedMerchants', []))} Merchants")

            if not plan:
                st.error("⚠️ No Action Plan matched.")

        with c2:
            st.markdown("### AI Diagnosis")
            hypothesis = plan.get("rootCauseHypothesis", "Analysis Pending...")
            st.markdown(f"> *{hypothesis}*")

            st.markdown("### Recommended Actions")
            actions = plan.get("recommendedActions", [])

            if not actions:
                st.warning("No automated actions generated.")
            else:
                for act in actions:
                    st.markdown(f"""
                    <div class="action-card">
                        <div class="card-header">{act.get('actionType', 'ACTION')}</div>
                        <div style="color: #CCCCCC;">{act.get('description', 'No details.')}</div>
                        <div style="margin-top:10px; font-size:0.85em; color: #888;">
                            Risk Level: <span style="color: #FFAB91;">{act.get('riskLevel', 'Unknown')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        cy, cn = st.columns(2)
        if cy.button("✅ Approve & Next", use_container_width=True):
            log_decision(iid_raw, "APPROVED", f"Approved {len(actions)} actions")
            st.session_state.incident_idx += 1
            st.rerun()
        if cn.button("❌ Reject & Next", use_container_width=True):
            log_decision(iid_raw, "REJECTED", "Operator rejected AI proposal")
            st.session_state.incident_idx += 1
            st.rerun()

# ---------------------------------------------------
# PAGE: TICKETS
# ---------------------------------------------------
elif st.session_state.page == "tickets":
    st.title("🎫 Ticket Desk")
    open_tickets = [t for t in tickets if t.get("status", "open") == "open"]

    if not open_tickets: st.info("No open tickets.")
    for t in open_tickets:
        tid = t.get("ticketId", "Unknown")
        mid = t.get("merchantId", "Unknown")
        issue = t.get("issueType", "General")

        with st.expander(f"📌 {issue} | Merchant: {mid}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"**ID:** {tid} | **Sev:** {t.get('severity', 'Normal')}")
                if st.button("Mark Resolved", key=f"c_{tid}"):
                    t["status"] = "closed"
                    save_data(TICKETS_FILE, tickets)
                    st.rerun()
            with c2:
                # Draft Logic
                draft = f"Dear Merchant ({mid}),\n\nSubject: Update on {issue}\n\n"
                if "login" in str(issue).lower():
                    draft += "We have reset your session."
                elif "payment" in str(issue).lower():
                    draft += "We are checking the payment gateway."
                else:
                    draft += "We are investigating your issue."

                subj = st.text_input("Subject", value=f"Re: {issue}", key=f"s_{tid}")
                body = st.text_area("Body", value=draft, height=100, key=f"b_{tid}")

                if st.button("Send & Save", key=f"sn_{tid}"):
                    outbox = load_data(EMAIL_OUTBOX_FILE)
                    outbox.append({
                        "ticket_id": tid, "merchant_id": mid, "body": body,
                        "subject": subj, "status": "queued",
                        "timestamp": datetime.now().isoformat()
                    })
                    save_data(EMAIL_OUTBOX_FILE, outbox)
                    st.success(f"Saved to {os.path.basename(EMAIL_OUTBOX_FILE)}!")

# ---------------------------------------------------
# PAGE: AUDIT
# ---------------------------------------------------
elif st.session_state.page == "audit":
    st.title("📜 Audit Log")
    logs = load_data(AUDIT_LOG_FILE)
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("No audit history found.")