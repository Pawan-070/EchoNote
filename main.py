from flask import Flask, request, render_template_string
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os, time, uuid, requests, tempfile, threading
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
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
          <li>The app transcribes it using AssemblyAI</li>
          <li>Get a shareable to-do list link shortly!</li>
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

def transcribe_with_assemblyai(audio_file_path):
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    headers = {
        "authorization": api_key
    }
    
    print("Uploading audio to AssemblyAI...")
    with open(audio_file_path, "rb") as audio_file:
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            data=audio_file,
            timeout=60
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"Upload failed: {upload_response.text}")
        
        audio_url = upload_response.json()["upload_url"]
        print(f"Audio uploaded: {audio_url}")
    
    print("Starting transcription...")
    transcription_payload = {
        "audio_url": audio_url,
        "language_code": "en"
    }
    
    transcription_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json=transcription_payload,
        timeout=60
    )
    
    if transcription_response.status_code != 200:
        raise Exception(f"Transcription request failed: {transcription_response.text}")
    
    transcript_id = transcription_response.json()["id"]
    print(f"Transcription ID: {transcript_id}")
    print("Waiting for transcription to complete...")
    
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    
    max_attempts = 60
    for attempt in range(max_attempts):
        polling_response = requests.get(polling_url, headers=headers, timeout=30)
        result = polling_response.json()
        
        status = result["status"]
        
        if status == "completed":
            print("Transcription complete!")
            return result["text"]
        elif status == "error":
            raise Exception(f"Transcription failed: {result.get('error')}")
        
        print(f"Status: {status}... waiting")
        time.sleep(2)
    
    raise Exception("Transcription timed out")

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
    host = request.host

    def job():
        try:
            time.sleep(5)
            print(f"Downloading audio from: {url}")
            auth = (os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
            audio_response = requests.get(url, auth=auth, timeout=30)
            audio_response.raise_for_status()
            audio = audio_response.content
            
            print(f"Downloaded {len(audio)} bytes")
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio)
                f.flush()
                temp_file = f.name
            
            print(f"Transcribing audio file: {temp_file}")
            text = transcribe_with_assemblyai(temp_file)
            
            os.unlink(temp_file)
            
            print(f"Transcription: {text}")
            lines = [x.strip() for x in text.replace(". ",".\n").split("\n") if x.strip()]
            id = str(uuid.uuid4())[:8]
            notes[id] = lines
            link = f"https://{host}/view/{id}"
            
            print(f"Sending link to {who}")
            twilio.messages.create(from_="whatsapp:+14155238886", to=who, body=f"Done! Open your list:\n{link}")
            print("Success!")
        except Exception as e:
            print(f"Error processing voice note: {e}")
            import traceback
            traceback.print_exc()
            try:
                twilio.messages.create(from_="whatsapp:+14155238886", to=who, body=f"Sorry, there was an error processing your voice note.")
            except:
                pass

    threading.Thread(target=job).start()
    resp.message("Processing your voice note... You'll get a link shortly!")
    return str(resp)

@app.route("/view/<id>")
def view(id):
    return render_template_string(HTML, lines=notes.get(id, ["No notes yet"]))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
