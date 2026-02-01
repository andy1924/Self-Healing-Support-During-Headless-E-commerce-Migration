import json
import os
import smtplib
import time
from email.message import EmailMessage
from datetime import datetime

# ===================== CONFIGURATION =====================
SENDER_EMAIL = "misalpaavv@gmail.com"
RECEIVER_EMAIL = "reciever28@gmail.com"
APP_PASSWORD = "yjiw qndx oers kkyi"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DELAY_SECONDS = 5  # Fast check for better responsiveness

# ===================== PATHS =====================
# These match your UI paths exactly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

INCIDENT_FILE = os.path.join(DATA_DIR, "incidents.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "auditLog.json")
# We track sent IDs in a separate JSON to avoid duplicates even if log is deleted
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_ids.json")
SENT_LOG_FILE = os.path.join(DATA_DIR, "sent_emails.log")


# ==============================================================

class DataManager:
    @staticmethod
    def load_json(filepath):
        if not os.path.exists(filepath): return []
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except:
            return []

    @staticmethod
    def save_json(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f: json.dump(data, f, indent=2)

    @staticmethod
    def append_to_log(filepath, timestamp, status, details):
        """Writes to the text log that the UI reads."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "a") as f:
            # UI expects: Time | Status | Details
            f.write(f"{timestamp} | {status} | {details}\n")


class ApprovalWatcher:
    @staticmethod
    def get_new_approved_incidents():
        """
        1. Reads Audit Log for APPROVED decisions.
        2. Filters out IDs we have already processed.
        """
        # Load Audit Log
        audit_logs = DataManager.load_json(AUDIT_LOG_FILE)

        # Load History of what we already sent
        processed_data = DataManager.load_json(PROCESSED_FILE)
        processed_ids = set(processed_data)

        approved_ids = set()

        for entry in audit_logs:
            if entry.get("decision") == "APPROVED":
                raw_id = entry.get("incident_id") or entry.get("incidentId")
                if raw_id:
                    clean_id = str(raw_id).strip().upper()
                    if clean_id not in processed_ids:
                        approved_ids.add(clean_id)

        return approved_ids


class EmailService:
    @staticmethod
    def send_email(incident_data):
        iid = incident_data.get('incidentId') or incident_data.get('id')
        issue = incident_data.get('issueType') or incident_data.get('issue')

        subject = f"[INCIDENT {iid}] Remediation Approved: {issue}"
        body = f"""
ACTION APPROVED.

Incident ID: {iid}
Issue Type: {issue}
Status: Remediation in Progress

The automated response plan has been authorized by the operator.
"""

        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.set_content(body.strip())

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.send_message(msg)
            return True, subject
        except Exception as e:
            print(f"   [Error] SMTP Failed: {e}")
            return False, str(e)


class MainLoop:
    @staticmethod
    def run():
        print(f"--- EMAIL SYNC SERVICE STARTED ---")
        print(f"Watching: {AUDIT_LOG_FILE}")
        print(f"Writing to: {SENT_LOG_FILE}")
        print("----------------------------------")

        while True:
            # 1. Find Approved but Unsent IDs
            approved_ids = ApprovalWatcher.get_new_approved_incidents()

            if approved_ids:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Found new approvals: {approved_ids}")

                # Load Incident Details
                all_incidents = DataManager.load_json(INCIDENT_FILE)
                processed_ids = DataManager.load_json(PROCESSED_FILE)

                for incident in all_incidents:
                    raw_id = incident.get("incidentId") or incident.get("id")
                    if not raw_id: continue

                    clean_id = str(raw_id).strip().upper()

                    # If this incident is in our "New Approvals" list
                    if clean_id in approved_ids:
                        print(f"   >>> Sending email for {clean_id}...")

                        success, info = EmailService.send_email(incident)

                        if success:
                            # A. Mark as Processed immediately so we don't double send
                            processed_ids.append(clean_id)
                            DataManager.save_json(PROCESSED_FILE, processed_ids)

                            # B. Update the UI Log
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            DataManager.append_to_log(SENT_LOG_FILE, timestamp, "SENT", info)
                            print("   ✅ Email Sent & Log Updated.")
                        else:
                            print("   ❌ Email Failed.")

            time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    try:
        MainLoop.run()
    except KeyboardInterrupt:
        print("\nService Stopped.")