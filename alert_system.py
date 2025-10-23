from twilio.rest import Client

def send_sms_alert(message, to_number, from_number, account_sid, auth_token):
    """
    Send SMS using Twilio
    """
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"❌ SMS Error: {e}")
        return False

# For email alert, you could later add SMTP (optional)
