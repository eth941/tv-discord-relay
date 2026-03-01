from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

@app.route("/webhook", methods=["POST"])
def webhook():
    message = request.get_data(as_text=True)
    if not message:
        return "No message", 400

    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK, json=payload)

    if response.status_code == 204:
        return "OK", 200
    else:
        return f"Discord error: {response.status_code}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
