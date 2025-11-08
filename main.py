from flask import Flask, request, render_template_string, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os, time, uuid, requests, tempfile, threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

app = Flask(__name__)
twilio = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
notes = {}
note_owners = {}

HTML = """
<!doctype html>
<html>
  <head>
    <title>Your Voice Plans</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 50%, #ef4444 100%);
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
        animation: slideUp 0.5s ease-out;
      }
      @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .header-section {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #f87171 100%);
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
        background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
        border: none;
        border-left: 5px solid #f43f5e;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) backwards;
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      .todo-item.completed {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 5px solid #0ea5e9;
      }
      .todo-item.completed .todo-text {
        text-decoration: line-through;
        color: #6b7280;
      }
      .todo-item:hover {
        transform: translateX(8px) scale(1.02);
        box-shadow: 0 8px 25px rgba(244, 63, 94, 0.4);
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px) scale(0.95); }
        to { opacity: 1; transform: translateY(0) scale(1); }
      }
      .todo-checkbox {
        width: 24px;
        height: 24px;
        cursor: pointer;
        flex-shrink: 0;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      .todo-checkbox:hover {
        transform: scale(1.15);
      }
      .todo-text {
        flex: 1;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      .todo-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
      }
      .todo-date {
        font-size: 0.85rem;
        color: #ef4444;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.3rem;
      }
      .date-input {
        padding: 0.4rem 0.6rem;
        border: 1px solid #fca5a5;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #dc2626;
        background: white;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .date-input:focus {
        outline: none;
        border-color: #ef4444;
        box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.1);
      }
      .delete-btn {
        background: transparent;
        color: #9ca3af;
        border: none;
        padding: 0.3rem;
        cursor: pointer;
        font-size: 1.1rem;
        transition: color 0.2s ease;
        flex-shrink: 0;
      }
      .delete-btn:hover {
        color: #ef4444;
      }
      .delete-btn:active {
        color: #dc2626;
      }
      .add-note-section {
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid #ef4444;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      .add-note-section:hover {
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2);
      }
      .add-note-input {
        width: 100%;
        padding: 0.8rem;
        border: 2px solid #fca5a5;
        border-radius: 8px;
        font-size: 1rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      .add-note-input:focus {
        outline: none;
        border-color: #ef4444;
        box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
        transform: scale(1.01);
      }
      .add-btn {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-size: 1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
      }
      .add-btn:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
      }
      .add-btn:active {
        transform: translateY(0) scale(0.98);
      }
      .share-btn {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
        width: 100%;
        margin-top: 1rem;
      }
      .share-btn:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.6);
      }
      .share-btn:active {
        transform: translateY(0) scale(0.98);
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
        z-index: 1000;
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
      .notice-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid #f59e0b;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        animation: slideDown 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
      }
      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .notice-box h6 {
        color: #92400e;
        font-weight: bold;
        margin: 0 0 0.8rem 0;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      .notice-box ul {
        margin: 0;
        padding-left: 1.2rem;
        color: #78350f;
        font-size: 0.9rem;
        line-height: 1.6;
      }
      .notice-box li {
        margin-bottom: 0.3rem;
      }
    </style>
  </head>
  <body>
    <div class="main-card">
      <div class="header-section">
        <h1>🎙️ Your Voice Plans</h1>
      </div>
      <div class="content-section">
        <div class="add-note-section">
          <h5 style="margin: 0 0 1rem 0; color: #991b1b;">✏️ Add New Note</h5>
          <input type="text" id="newNoteInput" class="add-note-input" placeholder="Type what you forgot to say...">
          <input type="date" id="newNoteDate" class="add-note-input" style="margin-bottom: 0.8rem;">
          <button class="add-btn" onclick="addNote()">+ Add Note</button>
        </div>

        <div id="todoList">
          {% if items %}
            {% for item in items %}
              <div class="todo-item {% if item.completed %}completed{% endif %}" data-index="{{ loop.index0 }}">
                <input type="checkbox" class="todo-checkbox" {% if item.completed %}checked{% endif %} onchange="toggleComplete({{ loop.index0 }})">
                <div class="todo-content">
                  <span class="todo-text">{{ item.text }}</span>
                  {% if item.date %}
                    <span class="todo-date">📅 {{ item.date }}</span>
                  {% endif %}
                </div>
                <button class="delete-btn" onclick="deleteNote({{ loop.index0 }})">🗑️</button>
              </div>
            {% endfor %}
          {% else %}
            <div class="empty-state">
              No notes yet. Add a note above or send a voice note to get started!
            </div>
          {% endif %}
        </div>

        <button class="share-btn" onclick="shareLink()">
          📤 Share This List
        </button>
      </div>
    </div>
    
    <div class="copy-notification" id="notification">
      ✅ Link copied to clipboard!
    </div>

    <script>
      const noteId = "{{ note_id }}";

      function addNote() {
        const input = document.getElementById('newNoteInput');
        const dateInput = document.getElementById('newNoteDate');
        const text = input.value.trim();
        const date = dateInput.value;
        
        if (!text) {
          alert('Please enter a note!');
          return;
        }

        fetch(`/api/notes/${noteId}/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text, date: date })
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            window.location.reload();
          }
        })
        .catch(err => console.error('Error:', err));
      }

      function deleteNote(index) {
        if (!confirm('Delete this note?')) return;

        fetch(`/api/notes/${noteId}/delete/${index}`, {
          method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            window.location.reload();
          }
        })
        .catch(err => console.error('Error:', err));
      }

      function toggleComplete(index) {
        fetch(`/api/notes/${noteId}/toggle/${index}`, {
          method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            window.location.reload();
          }
        })
        .catch(err => console.error('Error:', err));
      }

      document.getElementById('newNoteInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
          addNote();
        }
      });

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
    <title>Voice Plans App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 50%, #ef4444 100%);
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
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease-out backwards;
        border-left: 4px solid #ef4444;
      }
      .step-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
      }
      .step-card:nth-child(1) { animation-delay: 0.1s; }
      .step-card:nth-child(2) { animation-delay: 0.2s; }
      .step-card:nth-child(3) { animation-delay: 0.3s; }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .step-number {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
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
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4);
      }
      .info-box {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 4px solid #f87171;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: fadeIn 0.5s ease-out 0.4s backwards;
      }
      .status-box {
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
        border-left: 4px solid #dc2626;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: fadeIn 0.5s ease-out 0.5s backwards;
      }
      .webhook-url {
        background: #1e293b;
        color: #fca5a5;
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
        <h1>🎙️ Voice Plans App</h1>
        <p>Turn your voice notes into organized plans!</p>
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
          <span style="color: #dc2626;">Running and ready to receive voice notes!</span>
        </div>
      </div>
    </div>
  </body>
</html>
"""

def extract_date_from_text(text):
    """Extract date from text using OpenAI and return ISO format date string"""
    try:
        today = datetime.now()
        prompt = f"""Today is {today.strftime('%A, %B %d, %Y')}.

Extract the date mentioned in this text and return ONLY the date in YYYY-MM-DD format.
If no specific date is mentioned, return "none".

Examples:
- "meeting tomorrow" -> {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "doctor appointment on Friday" -> (calculate next Friday)
- "buy groceries on December 25th" -> 2025-12-25
- "call mom" -> none

Text: {text}

Return only the date in YYYY-MM-DD format or "none"."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        if result:
            result = result.strip()
        
        if not result or result.lower() == "none":
            return None
        
        # Validate date format
        datetime.strptime(result, '%Y-%m-%d')
        return result
        
    except Exception as e:
        print(f"Error extracting date: {e}")
        return None

def check_and_send_reminders():
    """Check for due tasks and send WhatsApp reminders"""
    from datetime import datetime
    today = datetime.now().date().isoformat()
    
    for note_id, items in notes.items():
        phone_number = note_owners.get(note_id)
        if not phone_number:
            continue
            
        due_tasks = []
        for item in items:
            if item.get("date") == today and not item.get("completed"):
                due_tasks.append(item["text"])
        
        if due_tasks:
            message = "🔔 Reminder! You have tasks due today:\n\n"
            for i, task in enumerate(due_tasks, 1):
                message += f"{i}. {task}\n"
            
            try:
                twilio.messages.create(
                    from_="whatsapp:+14155238886",
                    to=phone_number,
                    body=message
                )
                print(f"Sent reminder to {phone_number} for {len(due_tasks)} tasks")
            except Exception as e:
                print(f"Failed to send reminder: {e}")

def reminder_loop():
    """Background thread that checks for reminders every hour"""
    import time
    while True:
        try:
            check_and_send_reminders()
        except Exception as e:
            print(f"Error in reminder loop: {e}")
        time.sleep(3600)  # Check every hour

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
        time.sleep(1)
    
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
    
    tips_message = """💡 *Tips for Better Voice Notes*

📌 Speak slowly and steadily
📌 Pause briefly between sentences
📌 Record in a quiet environment
📌 Speak clearly and avoid mumbling

⏳ Processing your voice note... You'll get your link shortly!"""
    
    resp.message(tips_message)

    def job():
        try:
            time.sleep(1)
            print(f"Downloading audio from: {url}")
            twilio_sid = os.getenv("TWILIO_SID", "")
            twilio_token = os.getenv("TWILIO_TOKEN", "")
            audio_response = requests.get(url, auth=(twilio_sid, twilio_token), timeout=30)
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
            
            # Extract dates from each line
            tasks = []
            for line in lines:
                extracted_date = extract_date_from_text(line)
                tasks.append({
                    "text": line,
                    "completed": False,
                    "date": extracted_date
                })
                if extracted_date:
                    print(f"Extracted date '{extracted_date}' from: {line}")
            
            notes[id] = tasks
            note_owners[id] = who
            link = f"https://{host}/view/{id}"
            
            print(f"Sending link to {who}")
            try:
                twilio.messages.create(from_="whatsapp:+14155238886", to=who, body=f"Done! Open your list:\n{link}")
                print("Success! Link sent via WhatsApp")
            except Exception as twilio_error:
                print(f"⚠️ Twilio message failed: {twilio_error}")
                print(f"✅ But your transcription is ready!")
                print(f"🔗 YOUR LINK: {link}")
                print(f"📋 Transcription: {text[:100]}...")
        except Exception as e:
            print(f"Error processing voice note: {e}")
            import traceback
            traceback.print_exc()

    threading.Thread(target=job).start()
    return str(resp)

@app.route("/view/<id>")
def view(id):
    items = notes.get(id, [])
    return render_template_string(HTML, items=items, note_id=id)

@app.route("/api/notes/<id>/add", methods=["POST"])
def add_note(id):
    if id not in notes:
        return jsonify({"success": False, "error": "Note not found"}), 404
    
    data = request.get_json()
    text = data.get("text", "").strip()
    date = data.get("date", None)
    
    if not text:
        return jsonify({"success": False, "error": "Text is required"}), 400
    
    notes[id].append({"text": text, "completed": False, "date": date if date else None})
    return jsonify({"success": True})

@app.route("/api/notes/<id>/delete/<int:index>", methods=["POST"])
def delete_note(id, index):
    if id not in notes:
        return jsonify({"success": False, "error": "Note not found"}), 404
    
    if index < 0 or index >= len(notes[id]):
        return jsonify({"success": False, "error": "Invalid index"}), 400
    
    notes[id].pop(index)
    return jsonify({"success": True})

@app.route("/api/notes/<id>/toggle/<int:index>", methods=["POST"])
def toggle_note(id, index):
    if id not in notes:
        return jsonify({"success": False, "error": "Note not found"}), 404
    
    if index < 0 or index >= len(notes[id]):
        return jsonify({"success": False, "error": "Invalid index"}), 400
    
    notes[id][index]["completed"] = not notes[id][index]["completed"]
    return jsonify({"success": True})

if __name__ == "__main__":
    # Start reminder background thread
    reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()
    print("Reminder system started!")
    
    app.run(host="0.0.0.0", port=5000)
