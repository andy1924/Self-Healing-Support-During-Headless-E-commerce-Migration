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
CHECK_INTERVAL = 5  # Check for new approvals every 5 seconds

# ===================== PATHS =====================
# These paths match your UI structure exactly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

INCIDENT_FILE = os.path.join(DATA_DIR, "incidents.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "auditLog.json")
SENT_LOG_FILE = os.path.join(DATA_DIR, "sent_emails.log")
PROCESSED_TRACKER = os.path.join(DATA_DIR, "processed_ids.json")


# =================================================

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
    def append_to_ui_log(timestamp, status, subject):
        """Writes to the log file that the UI 'Sent Emails' page reads."""
        os.makedirs(os.path.dirname(SENT_LOG_FILE), exist_ok=True)
        with open(SENT_LOG_FILE, "a") as f:
            # UI expects: Time | Status | Details
            f.write(f"{timestamp} | {status} | {subject}\n")


class EmailService:
    @staticmethod
    def send_email(incident_id, issue_type):
        subject = f"[INCIDENT {incident_id}] Remediation Approved: {issue_type}"
        body = f"""
ACTION APPROVED.

Incident ID: {incident_id}
Issue: {issue_type}
Status: Remediation Started

The operator has authorized the automated action plan.
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
            print(f"   [SMTP Error] {e}")
            return False, str(e)


class Bot:
    @staticmethod
    def run():
        print("--- BACKGROUND EMAIL SENDER STARTED ---")
        print(f"Watching: {AUDIT_LOG_FILE}")
        print("---------------------------------------")

        while True:
            # 1. Load History (What we already sent)
            processed_ids = DataManager.load_json(PROCESSED_TRACKER)

            # 2. Load Approvals (What needs sending)
            audit_logs = DataManager.load_json(AUDIT_LOG_FILE)

            # 3. Find New Approvals
            for entry in audit_logs:
                if entry.get("decision") == "APPROVED":
                    raw_id = entry.get("incident_id")

                    if raw_id:
                        clean_id = str(raw_id).strip().upper()

                        # If this is APPROVED and NOT yet processed
                        if clean_id not in processed_ids:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] New Approval Found: {clean_id}")

                            # Fetch Incident Details for the email body
                            all_incidents = DataManager.load_json(INCIDENT_FILE)
                            issue_type = "General Issue"

                            # Find matching incident data
                            for inc in all_incidents:
                                inc_id_raw = inc.get("incidentId") or inc.get("id")
                                if inc_id_raw and str(inc_id_raw).strip().upper() == clean_id:
                                    issue_type = inc.get("issueType", "Unknown Issue")
                                    break

                            # SEND EMAIL
                            success, info = EmailService.send_email(clean_id, issue_type)

                            if success:
                                print(f"   ✅ Email Sent: {info}")

                                # A. Mark as processed so we don't send again
                                processed_ids.append(clean_id)
                                DataManager.save_json(PROCESSED_TRACKER, processed_ids)

                                # B. Update UI Log
                                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                DataManager.append_to_ui_log(ts, "SENT", info)
                            else:
                                print("   ❌ Failed to send.")

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # Optional: Uncomment the next line if you want to clear history and re-send everything
    # if os.path.exists(PROCESSED_TRACKER): os.remove(PROCESSED_TRACKER)

    try:
        Bot.run()
    except KeyboardInterrupt:
        print("\nStopped.")