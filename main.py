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
    <title>My Voice Notes To-Do List</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 2rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      .main-card {
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        max-width: 600px;
        margin: 0 auto;
        animation: slideUp 0.5s ease-out;
      }
      @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px 20px 0 0;
        text-align: center;
      }
      .header-section h1 {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
      }
      .content-section {
        padding: 2rem;
      }
      .todo-item {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: none;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out backwards;
      }
      .todo-item:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
      }
      .todo-item:nth-child(1) { animation-delay: 0.1s; }
      .todo-item:nth-child(2) { animation-delay: 0.2s; }
      .todo-item:nth-child(3) { animation-delay: 0.3s; }
      .todo-item:nth-child(4) { animation-delay: 0.4s; }
      .todo-item:nth-child(5) { animation-delay: 0.5s; }
      .share-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
        margin-top: 1rem;
      }
      .share-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
      }
      .share-btn:active {
        transform: translateY(0);
      }
      .copy-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        display: none;
        animation: slideInRight 0.3s ease-out;
      }
      @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      .empty-state {
        text-align: center;
        color: #6b7280;
        padding: 2rem;
        font-style: italic;
      }
    </style>
  </head>
  <body>
    <div class="main-card">
      <div class="header-section">
        <h1>🎙️ Your Voice Notes</h1>
      </div>
      <div class="content-section">
        {% if lines and lines[0] != "No notes yet" %}
          <div class="todo-list">
            {% for line in lines %}
              <div class="todo-item">
                ✓ {{ line }}
              </div>
            {% endfor %}
          </div>
          <button class="share-btn" onclick="shareLink()">
            📤 Share This List
          </button>
        {% else %}
          <div class="empty-state">
            No notes yet. Send a voice note to get started!
          </div>
        {% endif %}
      </div>
    </div>
    
    <div class="copy-notification" id="notification">
      ✅ Link copied to clipboard!
    </div>

    <script>
      function shareLink() {
        const url = window.location.href;
        
        if (navigator.share) {
          navigator.share({
            title: 'My Voice Notes To-Do List',
            text: 'Check out my voice notes!',
            url: url
          }).catch(() => {
            copyToClipboard(url);
          });
        } else {
          copyToClipboard(url);
        }
      }
      
      function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
          showNotification();
        }).catch(() => {
          const textarea = document.createElement('textarea');
          textarea.value = text;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
          showNotification();
        });
      }
      
      function showNotification() {
        const notification = document.getElementById('notification');
        notification.style.display = 'block';
        setTimeout(() => {
          notification.style.display = 'none';
        }, 3000);
      }
    </script>
  </body>
</html>
"""

HOME_HTML = """
<!doctype html>
<html>
  <head>
    <title>Voice Notes To-Do App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 2rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      .main-card {
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        max-width: 700px;
        margin: 0 auto;
        animation: slideUp 0.6s ease-out;
      }
      @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px 20px 0 0;
        text-align: center;
      }
      .header-section h1 {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0 0 1rem 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        animation: pulse 2s ease-in-out infinite;
      }
      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
      }
      .header-section p {
        font-size: 1.2rem;
        margin: 0;
        opacity: 0.95;
      }
      .content-section {
        padding: 2rem;
      }
      .step-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out backwards;
      }
      .step-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
      }
      .step-card:nth-child(1) { animation-delay: 0.1s; }
      .step-card:nth-child(2) { animation-delay: 0.2s; }
      .step-card:nth-child(3) { animation-delay: 0.3s; }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .step-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
      }
      .info-box {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 4px solid #0ea5e9;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: fadeIn 0.5s ease-out 0.4s backwards;
      }
      .status-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: fadeIn 0.5s ease-out 0.5s backwards;
      }
      .webhook-url {
        background: #1e293b;
        color: #10b981;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
        word-break: break-all;
        margin: 0.5rem 0;
        display: block;
      }
      strong {
        color: #1e293b;
      }
      .icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
      }
    </style>
  </head>
  <body>
    <div class="main-card">
      <div class="header-section">
        <h1>🎙️ Voice Notes To-Do App</h1>
        <p>Turn your voice notes into organized to-do lists!</p>
      </div>
      <div class="content-section">
        <h4 style="color: #1e293b; margin-bottom: 1.5rem;">✨ How it works:</h4>
        
        <div class="step-card">
          <span class="step-number">1</span>
          <strong>Send a Voice Note</strong>
          <p style="margin: 0.5rem 0 0 3.5rem; color: #4b5563;">
            Record and send a voice message to your Twilio WhatsApp number
          </p>
        </div>
        
        <div class="step-card">
          <span class="step-number">2</span>
          <strong>AI Transcription</strong>
          <p style="margin: 0.5rem 0 0 3.5rem; color: #4b5563;">
            Our AI automatically transcribes your voice to text using AssemblyAI
          </p>
        </div>
        
        <div class="step-card">
          <span class="step-number">3</span>
          <strong>Get Shareable Link</strong>
          <p style="margin: 0.5rem 0 0 3.5rem; color: #4b5563;">
            Receive a beautiful shareable link to your organized to-do list!
          </p>
        </div>
        
        <div class="info-box">
          <strong><span class="icon">🔗</span>Webhook URL:</strong><br>
          <code class="webhook-url">https://{{ request.host }}/webhook</code>
          <p style="margin: 0.5rem 0 0 0; color: #64748b; font-size: 0.9rem;">
            Configure this in your Twilio WhatsApp Sandbox settings
          </p>
        </div>
        
        <div class="status-box">
          <strong><span class="icon">✅</span>App Status:</strong> 
          <span style="color: #059669;">Running and ready to receive voice notes!</span>
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
