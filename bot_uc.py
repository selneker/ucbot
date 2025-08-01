import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

# ENV Variables
VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# Facebook verification route
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token"

# Facebook message receiver
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    user_message = messaging_event["message"]["text"]
                    # Get response from ChatGPT
                    response = ask_chatgpt(user_message)
                    # Send response back to user
                    send_message(sender_id, response)
    return "ok", 200

def ask_chatgpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # na "gpt-4" raha manana
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v17.0/me/messages"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}
    requests.post(url, headers=headers, params=params, json=data)

if __name__ == "__main__":
    app.run(debug=True)
