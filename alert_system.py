from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def send_flood_alert(message):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_PHONE"),
        to=os.getenv("ALERT_PHONE")
    )
