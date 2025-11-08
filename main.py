
from flask import Flask, request, render_template_string
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os, time, uuid, requests, subprocess, tempfile, threading
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
openai = OpenAI(api_key=os.getenv("OPENAI_KEY"))
twilio = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
notes = {}

HTML = """
<!doctype html>
<html>
  <head>
    <title>My To-Do List</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light p-5">
    <div class="card mx-auto" style="max-width:500px;">
      <div class="card-body">
        <h2 class="text-center">Your Voice Notes</h2>
        <ul class="list-group">
          {% for line in lines %}
            <li class="list-group-item">{{ line }}</li>
          {% endfor %}
        </ul>
        <p class="text-center mt-3">Share this link!</p>
      </div>
    </div>
  </body>
</html>
"""

HOME_HTML = """
<!doctype html>
<html>
  <head>
    <title>Voice Notes App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light p-5">
    <div class="card mx-auto" style="max-width:600px;">
      <div class="card-body">
        <h1 class="text-center mb-4">🎙️ Voice Notes To-Do App</h1>
        <p class="lead">Turn your voice notes into organized to-do lists!</p>
        
        <h5 class="mt-4">How it works:</h5>
        <ol>
          <li>Send a voice note to your Twilio WhatsApp number</li>
          <li>The app transcribes it using OpenAI Whisper</li>
          <li>Get a shareable to-do list link in 2 minutes</li>
        </ol>
        
        <div class="alert alert-info mt-4">
          <strong>Webhook URL:</strong><br>
          <code>https://{{ request.host }}/webhook</code>
          <p class="mb-0 mt-2"><small>Configure this in your Twilio WhatsApp Sandbox settings</small></p>
        </div>
        
        <div class="alert alert-success mt-3">
          <strong>✅ App Status:</strong> Running and ready to receive voice notes!
        </div>
      </div>
    </div>
  </body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/webhook", methods=["POST"])
def webhook():
    resp = MessagingResponse()
    if not request.form.get("NumMedia") == "1":
        resp.message("Send ONE voice note")
        return str(resp)

    url = request.form["MediaUrl0"]
    who = request.form["From"]

    def job():
        time.sleep(120)  
        audio = requests.get(url).content
        with tempfile.NamedTemporaryFile(suffix=".ogg") as f1:
            f1.write(audio); f1.flush()
            with tempfile.NamedTemporaryFile(suffix=".wav") as f2:
                subprocess.run(["ffmpeg","-y","-i",f1.name,"-ar","16000","-ac","1",f2.name], check=True)
                text = openai.audio.transcriptions.create(model="whisper-1", file=open(f2.name,"rb")).text
        lines = [x.strip() for x in text.replace(". ",".\n").split("\n") if x.strip()]
        id = str(uuid.uuid4())[:8]
        notes[id] = lines
        link = f"https://{request.host}/view/{id}"
        twilio.messages.create(from_="whatsapp:+14155238886", to=who, body=f"Done! Open your list:\n{link}")

    threading.Thread(target=job).start()
    resp.message("Recording… I’ll send the link in 2 minutes!")
    return str(resp)

@app.route("/view/<id>")
def view(id):
    return render_template_string(HTML, lines=notes.get(id, ["No notes yet"]))

app.run(host="0.0.0.0", port=5000)