import json
import time
import os
from datetime import datetime

# ---------------------------------------------------
# Configuration
# ---------------------------------------------------
OUTBOX_FILE = "emailOutbox.json"
SENT_LOG_FILE = "sent_emails.log"


def load_outbox():
    if not os.path.exists(OUTBOX_FILE):
        return []
    try:
        with open(OUTBOX_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_outbox(data):
    with open(OUTBOX_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_sent_email(email_data):
    """Appends the sent email details to a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] SENT TO: {email_data.get('merchantId')} | "
        f"SUBJECT: {email_data.get('subject')}\n"
    )

    with open(SENT_LOG_FILE, "a") as f:
        f.write(log_entry)


def send_email_mock(email):
    """
    Mock function to simulate sending an email.
    Replace this with smtplib or an API call in production.
    """
    print(f"\n{'=' * 40}")
    print(f"🚀 SENDING EMAIL...")
    print(f"To:      {email.get('merchantId')}")
    print(f"Subject: {email.get('subject')}")
    print(f"Body:    {email.get('body')}")
    print(f"{'=' * 40}\n")

    # Simulate network delay
    time.sleep(1.5)
    return True


def process_outbox():
    print("Checking Outbox for pending emails...")
    outbox = load_outbox()

    # Filter for emails that are 'queued' or haven't been sent yet
    # (Assuming the UI saves them with status='queued')
    pending_emails = [e for e in outbox if e.get("status") == "queued"]

    if not pending_emails:
        print("📭 Outbox is empty. No emails to send.")
        return

    print(f"📬 Found {len(pending_emails)} pending emails.")

    processed_count = 0
    remaining_emails = []

    # Process pending
    for email in pending_emails:
        success = send_email_mock(email)
        if success:
            log_sent_email(email)
            email["status"] = "sent"
            email["sent_at"] = datetime.now().isoformat()
            processed_count += 1
        else:
            # If failed, keep it in the list to retry later
            remaining_emails.append(email)

    # Keep already sent emails in the file (history) or archive them?
    # For now, we update the main list with the new statuses

    # Update the original list in memory
    for i, original_email in enumerate(outbox):
        if original_email.get("status") == "queued":
            # We assume strict ordering or use ID matching in a real DB
            # For this simple JSON, we just marked the pending ones as sent above
            pass

    # Save the updated status back to the JSON file
    save_outbox(outbox)

    print(f"✅ Successfully sent {processed_count} emails.")


if __name__ == "__main__":
    # You can run this in a loop or as a cron job
    while True:
        process_outbox()
        print("Sleeping for 10 seconds...")
        time.sleep(10)