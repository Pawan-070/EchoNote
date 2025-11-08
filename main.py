from flask import Flask, request, render_template_string, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os, time, uuid, requests, tempfile, threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
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
        font-size: 0.75rem;
        color: white;
        background: #ef4444;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        margin-top: 0.3rem;
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
      .add-note-toggle {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        margin-bottom: 1.5rem;
      }
      .add-note-toggle:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
      }
      .add-note-toggle:active {
        transform: translateY(0);
      }
      .add-note-form {
        display: none;
        animation: slideDown 0.3s ease-out;
      }
      .add-note-form.active {
        display: block;
      }
      @keyframes slideDown {
        from {
          opacity: 0;
          transform: translateY(-10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
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
        <button class="add-note-toggle" onclick="toggleAddForm()">
          ✏️ Add New Note
        </button>
        
        <div id="addNoteForm" class="add-note-section add-note-form">
          <h5 style="margin: 0 0 1rem 0; color: #991b1b;">✏️ Create New Note</h5>
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
                    <div class="todo-date">📅 {{ item.date }}</div>
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

      function toggleAddForm() {
        const form = document.getElementById('addNoteForm');
        form.classList.toggle('active');
      }

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
    <title>Voice Plans - Flora Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #bbf7d0 100%);
        min-height: 100vh;
        padding: 2rem 1rem;
        font-family: 'Inter', -apple-system, sans-serif;
        color: #1e3a1e;
      }
      
      .container {
        max-width: 900px;
        margin: 0 auto;
      }
      
      /* Header with Flora Theme */
      .hero-section {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        border-radius: 24px;
        padding: 3rem 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(5, 150, 105, 0.25);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
      }
      
      .hero-section::before {
        content: '🌿';
        position: absolute;
        font-size: 8rem;
        opacity: 0.1;
        top: -1rem;
        left: 2rem;
      }
      
      .hero-section::after {
        content: '🍃';
        position: absolute;
        font-size: 6rem;
        opacity: 0.1;
        bottom: -1rem;
        right: 2rem;
      }
      
      .hero-section h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
      }
      
      .hero-section p {
        font-size: 1.2rem;
        color: #d1fae5;
        font-weight: 400;
      }
      
      /* Section Container */
      .section-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(5, 150, 105, 0.08);
        border: 1px solid #d1fae5;
      }
      
      .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #047857;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .section-title::before {
        content: '';
        width: 4px;
        height: 28px;
        background: linear-gradient(180deg, #059669 0%, #10b981 100%);
        border-radius: 2px;
      }
      
      /* How It Works Steps */
      .steps-container {
        display: grid;
        gap: 1rem;
      }
      
      .step-item {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-radius: 16px;
        padding: 1.5rem;
        border-left: 4px solid #10b981;
        transition: all 0.3s ease;
        position: relative;
      }
      
      .step-item:hover {
        transform: translateX(8px);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
      }
      
      .step-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.75rem;
      }
      
      .step-number {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
      }
      
      .step-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #065f46;
      }
      
      .step-description {
        color: #374151;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-left: 3rem;
      }
      
      /* Technical Setup Section */
      .tech-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
      }
      
      .tech-box h5 {
        color: #92400e;
        font-weight: 600;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .webhook-url {
        background: #1e293b;
        color: #86efac;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        word-break: break-all;
        margin: 0.75rem 0;
        display: block;
        border: 2px solid #334155;
      }
      
      /* Features Grid */
      .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
      }
      
      .feature-item {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #a7f3d0;
        transition: all 0.3s ease;
      }
      
      .feature-item:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.15);
      }
      
      .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
      }
      
      .feature-title {
        font-weight: 600;
        color: #065f46;
        margin-bottom: 0.25rem;
      }
      
      .feature-desc {
        font-size: 0.85rem;
        color: #374151;
      }
      
      /* Status Indicator */
      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
      }
      
      .status-dot {
        width: 8px;
        height: 8px;
        background: #d1fae5;
        border-radius: 50%;
        animation: pulse 2s infinite;
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.2); }
      }
      
      /* Calendar Section */
      .calendar-badge {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      
      .calendar-badge strong {
        color: #1e40af;
      }
      
      @media (max-width: 768px) {
        .hero-section h1 {
          font-size: 2rem;
        }
        
        .features-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <!-- Hero Section -->
      <div class="hero-section">
        <h1>🌿 Voice Plans</h1>
        <p>Transform your thoughts into organized plans, naturally</p>
      </div>
      
      <!-- How It Works -->
      <div class="section-card">
        <h2 class="section-title">How It Works</h2>
        <div class="steps-container">
          <div class="step-item">
            <div class="step-header">
              <div class="step-number">1</div>
              <div class="step-title">🎤 Record Your Thoughts</div>
            </div>
            <p class="step-description">
              Send a voice note via WhatsApp to your Twilio number. Speak naturally about your tasks and plans.
            </p>
          </div>
          
          <div class="step-item">
            <div class="step-header">
              <div class="step-number">2</div>
              <div class="step-title">🤖 AI Transcription</div>
            </div>
            <p class="step-description">
              Our AI transcribes your voice with AssemblyAI, extracts dates/times, and organizes everything automatically.
            </p>
          </div>
          
          <div class="step-item">
            <div class="step-header">
              <div class="step-number">3</div>
              <div class="step-title">📋 Get Organized</div>
            </div>
            <p class="step-description">
              Receive a beautiful shareable link with your tasks categorized and ready to manage!
            </p>
          </div>
        </div>
      </div>
      
      <!-- Features Section -->
      <div class="section-card">
        <h2 class="section-title">🌟 Features</h2>
        <div class="features-grid">
          <div class="feature-item">
            <span class="feature-icon">✅</span>
            <div class="feature-title">Smart Checkboxes</div>
            <div class="feature-desc">Check off completed tasks with satisfying animations</div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">📅</span>
            <div class="feature-title">Date Detection</div>
            <div class="feature-desc">AI extracts dates and times automatically</div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">📂</span>
            <div class="feature-title">Auto Categories</div>
            <div class="feature-desc">Tasks organized by type for easy management</div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">📆</span>
            <div class="feature-title">Calendar Sync</div>
            <div class="feature-desc">Google Calendar integration with smart scheduling</div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">🔗</span>
            <div class="feature-title">Shareable Links</div>
            <div class="feature-desc">Unique URLs for every voice note</div>
          </div>
          
          <div class="feature-item">
            <span class="feature-icon">🌿</span>
            <div class="feature-title">Flora Design</div>
            <div class="feature-desc">Beautiful, calming interface</div>
          </div>
        </div>
      </div>
      
      <!-- Technical Setup -->
      <div class="section-card">
        <h2 class="section-title">⚙️ Setup</h2>
        <div class="tech-box">
          <h5>🔗 Webhook Configuration</h5>
          <code class="webhook-url">https://{{ request.host }}/webhook</code>
          <p style="margin: 0.5rem 0 0 0; color: #78350f; font-size: 0.9rem;">
            Configure this URL in your Twilio WhatsApp Sandbox settings
          </p>
        </div>
        
        <div class="calendar-badge">
          <span style="font-size: 1.5rem;">📆</span>
          <div>
            <strong>Google Calendar Integration:</strong>
            <div style="font-size: 0.9rem; margin-top: 0.25rem;">
              Visit <a href="/auth" style="color: #1e40af; font-weight: 600;">/auth</a> to connect your calendar
            </div>
          </div>
        </div>
      </div>
      
      <!-- Status -->
      <div class="section-card" style="text-align: center;">
        <div class="status-badge">
          <span class="status-dot"></span>
          <span>App Running & Ready</span>
        </div>
      </div>
    </div>
  </body>
</html>
"""

def extract_datetime_from_text(text):
    """Extract date and time from text using OpenAI and return structured data"""
    try:
        today = datetime.now()
        prompt = f"""Today is {today.strftime('%A, %B %d, %Y')} at {today.strftime('%H:%M')}.

Extract the date and time mentioned in this text. Return in this exact format:
DATE: YYYY-MM-DD
TIME: HH:MM
If no date is mentioned, write "DATE: none"
If no time is mentioned, write "TIME: none"

Examples:
- "meeting tomorrow at 3pm" -> DATE: {(today + timedelta(days=1)).strftime('%Y-%m-%d')}\nTIME: 15:00
- "doctor appointment Friday 2pm" -> DATE: (next Friday)\nTIME: 14:00
- "buy groceries December 25th" -> DATE: 2025-12-25\nTIME: none
- "call mom at 5:30 PM" -> DATE: none\nTIME: 17:30
- "just a note" -> DATE: none\nTIME: none

Text: {text}

Return in the exact format shown above."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        if not result:
            return None, None
        
        result = result.strip()
        date_val = None
        time_val = None
        
        # Parse the response
        for line in result.split('\n'):
            if line.startswith('DATE:'):
                date_str = line.replace('DATE:', '').strip()
                if date_str.lower() != 'none':
                    try:
                        datetime.strptime(date_str, '%Y-%m-%d')
                        date_val = date_str
                    except:
                        pass
            elif line.startswith('TIME:'):
                time_str = line.replace('TIME:', '').strip()
                if time_str.lower() != 'none':
                    try:
                        datetime.strptime(time_str, '%H:%M')
                        time_val = time_str
                    except:
                        pass
        
        return date_val, time_val
        
    except Exception as e:
        print(f"Error extracting datetime: {e}")
        return None, None

def get_calendar_service():
    """Get authenticated Google Calendar service (non-blocking)"""
    try:
        import pickle
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        # Only proceed if we already have valid credentials
        if not os.path.exists('token.pickle'):
            print("token.pickle not found. Run /auth endpoint first to authenticate.")
            return None
        
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        if not creds or not creds.valid:
            print("Credentials invalid. Re-authenticate at /auth endpoint.")
            return None
        
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error getting calendar service: {e}")
        return None

def create_calendar_event(task_text, date_str, time_str=None, timezone='America/New_York'):
    """Create a Google Calendar event for a task"""
    try:
        service = get_calendar_service()
        if not service:
            print("Calendar service not available")
            return False
        
        # Build event time
        if time_str:
            start_datetime = f"{date_str}T{time_str}:00"
            # Default 1-hour duration
            end_time = datetime.strptime(time_str, '%H:%M') + timedelta(hours=1)
            end_datetime = f"{date_str}T{end_time.strftime('%H:%M')}:00"
            
            event = {
                'summary': task_text,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': timezone,
                },
                'description': 'Created from Voice Plans App'
            }
        else:
            # All-day event - end date must be next day (exclusive)
            end_date = (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            event = {
                'summary': task_text,
                'start': {
                    'date': date_str,
                },
                'end': {
                    'date': end_date,
                },
                'description': 'Created from Voice Plans App'
            }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"✓ Calendar event created: {created_event.get('htmlLink')}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating calendar event: {e}")
        return False

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

@app.route("/auth")
def authenticate_calendar():
    """Start Google Calendar OAuth flow"""
    try:
        from google_auth_oauthlib.flow import Flow
        from flask import session
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        if not os.path.exists('credentials.json'):
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; background: #fee2e2;">
                <h2 style="color: #dc2626;">❌ credentials.json not found</h2>
                <p>Please upload your Google Calendar credentials.json file to enable calendar integration.</p>
                <p>See CALENDAR_SETUP.md for instructions.</p>
            </body>
            </html>
            """
        
        # Force HTTPS for redirect URI (Replit uses HTTPS)
        redirect_uri = request.url_root.replace('http://', 'https://').rstrip('/') + '/auth/callback'
        
        # Create flow with proper redirect URI
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Store state in Flask session
        session['oauth_state'] = state
        
        # Redirect user to Google's OAuth page
        return f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url={authorization_url}">
        </head>
        <body style="font-family: Arial; padding: 40px; background: #fef2f2;">
            <h2 style="color: #dc2626;">Redirecting to Google...</h2>
            <p>If you're not redirected, <a href="{authorization_url}">click here</a>.</p>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; background: #fef2f2;">
            <h2 style="color: #dc2626;">❌ Error starting authentication</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/" style="color: #dc2626; font-weight: bold;">← Back to Home</a></p>
        </body>
        </html>
        """

@app.route("/auth/callback")
def auth_callback():
    """Handle OAuth callback from Google"""
    try:
        import pickle
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        from flask import session
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        # Get state from session
        state = session.get('oauth_state')
        if not state:
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; background: #fef2f2;">
                <h2 style="color: #dc2626;">❌ Session expired</h2>
                <p>Please <a href="/auth">restart authentication</a>.</p>
            </body>
            </html>
            """
        
        # Reconstruct the flow with the same redirect URI
        redirect_uri = request.url_root.replace('http://', 'https://').rstrip('/') + '/auth/callback'
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            state=state,
            redirect_uri=redirect_uri
        )
        
        # Exchange authorization code for credentials
        # Force HTTPS in the authorization response URL
        authorization_response = request.url.replace('http://', 'https://')
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
        # Test the connection
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendars().get(calendarId='primary').execute()
        
        # Clear session
        session.pop('oauth_state', None)
        
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; background: #dcfce7;">
            <h2 style="color: #16a34a;">✅ Successfully connected to Google Calendar!</h2>
            <p><strong>Calendar:</strong> {calendar.get('summary', 'Primary Calendar')}</p>
            <p>Your voice notes with dates/times will now automatically sync to your calendar.</p>
            <p><a href="/" style="color: #dc2626; font-weight: bold;">← Back to Home</a></p>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; background: #fef2f2;">
            <h2 style="color: #dc2626;">❌ Authentication failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Please <a href="/auth">try again</a> or check CALENDAR_SETUP.md for troubleshooting.</p>
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
            
            # Extract dates and times from each line
            tasks = []
            for line in lines:
                extracted_date, extracted_time = extract_datetime_from_text(line)
                tasks.append({
                    "text": line,
                    "completed": False,
                    "date": extracted_date,
                    "time": extracted_time
                })
                if extracted_date or extracted_time:
                    print(f"Extracted date='{extracted_date}', time='{extracted_time}' from: {line}")
                
                # Create Google Calendar event if date is present
                if extracted_date:
                    calendar_success = create_calendar_event(line, extracted_date, extracted_time)
                    if calendar_success:
                        print(f"✓ Added to Google Calendar: {line}")
                    else:
                        print(f"✗ Could not add to Google Calendar (not configured or error)")

            
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
    
    notes[id].append({"text": text, "completed": False, "date": date if date else None, "time": None})
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
