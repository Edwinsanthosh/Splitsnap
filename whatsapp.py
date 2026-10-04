from flask import Flask, request
from twilio.rest import Client
import os


app = Flask(__name__)


# ============================================================
# TWILIO CONFIGURATION
# ============================================================

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_WHATSAPP_NUMBER = os.getenv(
    "TWILIO_WHATSAPP_NUMBER"
)

TWILIO_CONTENT_SID = os.getenv(
    "TWILIO_CONTENT_SID"
)


# ============================================================
# TWILIO CLIENT
# ============================================================

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)


# ============================================================
# WHATSAPP WEBHOOK
# ============================================================

@app.route("/whatsapp", methods=["POST"])
def whatsapp():

    incoming_message = request.values.get(
        "Body",
        ""
    ).strip()

    sender = request.values.get(
        "From",
        ""
    )

    print("================================")
    print("WhatsApp Message Received")
    print("From:", sender)
    print("Message:", incoming_message)
    print("================================")


    try:

        # ----------------------------------------------------
        # Send WhatsApp message through Twilio API
        # ----------------------------------------------------

        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=sender,
            content_sid=TWILIO_CONTENT_SID
        )

        print("Message sent successfully!")
        print("Message SID:", message.sid)

        return "Message sent", 200


    except Exception as error:

        print("================================")
        print("TWILIO ERROR")
        print(error)
        print("================================")

        return "Failed to send message", 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )