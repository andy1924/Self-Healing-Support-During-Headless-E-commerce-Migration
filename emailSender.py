import json
import os
import smtplib
import re
import time
from email.message import EmailMessage
from datetime import datetime

# ===================== CONFIGURATION =====================
SENDER_EMAIL = "misalpaavv@gmail.com"
RECEIVER_EMAIL = "reciever28@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
APP_PASSWORD = "yjiw qndx oers kkyi"
DELAY_SECONDS = 15  # <--- SET DELAY HERE

# ===================== PATHS =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

INCIDENT_FILE = os.path.join(DATA_DIR, "incidents.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "auditLog.json")
OUTBOX_FILE = os.path.join(DATA_DIR, "emailOutbox.json")
LOG_FILE = os.path.join(DATA_DIR, "sent_emails.log")


# ==============================================================

class DataManager:
    @staticmethod
    def load_json(filepath):
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    @staticmethod
    def save_json(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)


class ApprovalGatekeeper:
    @staticmethod
    def get_approved_ids_set():
        logs = DataManager.load_json(AUDIT_LOG_FILE)
        approved_ids = set()
        for entry in logs:
            if entry.get("decision") == "APPROVED":
                raw_id = entry.get("incident_id") or entry.get("incidentId")
                if raw_id:
                    clean_id = str(raw_id).strip().lower()
                    approved_ids.add(clean_id)
        return approved_ids


class OutboxManager:
    @staticmethod
    def is_successfully_processed(incident_id):
        outbox = DataManager.load_json(OUTBOX_FILE)
        target = str(incident_id).strip().lower()

        for email in outbox:
            eid = str(email.get("incident_id", "")).strip().lower()
            # Subject Fallback
            if not eid:
                match = re.search(r"incident\s+([a-zA-Z0-9-]+)", email.get("subject", ""), re.IGNORECASE)
                if match:
                    eid = match.group(1).strip().lower()

            if eid == target:
                status = email.get("status", "")
                if status in ["sent", "queued"]:
                    return True
        return False

    @staticmethod
    def queue_email(email_data):
        outbox = DataManager.load_json(OUTBOX_FILE)
        outbox.append(email_data)
        DataManager.save_json(OUTBOX_FILE, outbox)


class EmailComposer:
    @staticmethod
    def create_draft(incident):
        iid = incident.get('incidentId') or incident.get('id')
        issue = incident.get('issueType') or incident.get('issue')
        status = incident.get('status', 'Open')

        subject = f"[INCIDENT {iid}] Remediation Approved: {issue}"
        body = f"""
ACTION APPROVED for Incident {iid}.

Issue: {issue}
Status: {status}

The system has received operator approval and is executing the resolution plan.
"""
        return {
            "incident_id": str(iid).strip(),
            "to": RECEIVER_EMAIL,
            "subject": subject,
            "body": body.strip(),
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }


class MailSender:
    @staticmethod
    def send_verified_emails():
        outbox = DataManager.load_json(OUTBOX_FILE)
        if not outbox: return

        approved_ids = ApprovalGatekeeper.get_approved_ids_set()
        sent_count = 0
        updated_outbox = []

        for email in outbox:
            if email.get("status") == "queued":
                eid = str(email.get("incident_id", "")).strip().lower()

                # Subject fallback
                if not eid:
                    match = re.search(r"incident\s+([a-zA-Z0-9-]+)", email.get("subject", ""), re.IGNORECASE)
                    if match: eid = match.group(1).strip().lower()

                if not eid or eid not in approved_ids:
                    print(f"   ⚠️ Skipping {eid} (Unapproved)")
                    # Keeps status as 'queued' to retry later if approval comes in
                else:
                    if MailSender._dispatch(email):
                        email["status"] = "sent"
                        email["sent_at"] = datetime.now().isoformat()
                        sent_count += 1
                        print(f"   🚀 SENT email for: {eid}")

            updated_outbox.append(email)

        DataManager.save_json(OUTBOX_FILE, updated_outbox)

    @staticmethod
    def _dispatch(email):
        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email["to"]
        msg["Subject"] = email["subject"]
        msg.set_content(email["body"])

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.send_message(msg)

            with open(LOG_FILE, "a") as f:
                f.write(f"{datetime.now()} | SENT | {email['subject']}\n")
            return True
        except Exception as e:
            print(f"   ❌ SMTP Error: {e}")
            return False


class ServiceLoop:
    @staticmethod
    def run_forever():
        print(f"--- STARTING EMAIL SERVICE (Check every {DELAY_SECONDS}s) ---")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                ServiceLoop.tick()
                time.sleep(DELAY_SECONDS)
        except KeyboardInterrupt:
            print("\n--- STOPPING SERVICE ---")

    @staticmethod
    def tick():
        # 1. Get Approvals
        approved_ids = ApprovalGatekeeper.get_approved_ids_set()

        # 2. Check for NEW approvals to queue
        all_incidents = DataManager.load_json(INCIDENT_FILE)
        new_queued = 0

        for incident in all_incidents:
            raw_id = incident.get("incidentId") or incident.get("id")
            if not raw_id: continue
            clean_id = str(raw_id).strip().lower()

            if clean_id in approved_ids:
                if not OutboxManager.is_successfully_processed(clean_id):
                    draft = EmailComposer.create_draft(incident)
                    OutboxManager.queue_email(draft)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ➕ New Approval Detected: Queued {raw_id}")
                    new_queued += 1

        # 3. Send Pending
        if new_queued > 0:
            MailSender.send_verified_emails()
        else:
            # Check if there are any pending in outbox that need sending
            # (e.g. if previous send failed)
            MailSender.send_verified_emails()

        # Optional heartbeat print so you know it's alive
        # print(f".", end="", flush=True)


if __name__ == "__main__":
    ServiceLoop.run_forever()