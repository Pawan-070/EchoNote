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
    <title>✨ EchoNote</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        background: linear-gradient(135deg, #F9FAFB 0%, #E0F2FE 100%);
        min-height: 100vh;
        padding: 1.5rem;
        font-family: 'Inter', -apple-system, sans-serif;
        color: #0F172A;
      }
      
      .container {
        max-width: 800px;
        margin: 0 auto;
      }
      
      /* Hero Header */
      .hero-header {
        background: linear-gradient(135deg, #0F766E 0%, #334155 100%);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(15, 118, 110, 0.25);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
      }
      
      .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 20% 50%, rgba(56, 189, 248, 0.1), transparent 70%);
        pointer-events: none;
      }
      
      .hero-header h1 {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        text-shadow: 0 2px 12px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
      }
      
      /* Add Note Button */
      .add-note-toggle {
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
        margin-bottom: 1.5rem;
      }
      
      .add-note-toggle:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4);
      }
      
      /* Add Note Form */
      .add-note-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(15, 118, 110, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.2);
        backdrop-filter: blur(10px);
        display: none;
        animation: slideDown 0.3s ease-out;
      }
      
      .add-note-section.active {
        display: block;
      }
      
      @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .add-note-section h5 {
        color: #0F766E;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .add-note-input {
        width: 100%;
        padding: 0.9rem;
        border: 2px solid #E0F2FE;
        border-radius: 12px;
        font-size: 1rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        background: white;
      }
      
      .add-note-input:focus {
        outline: none;
        border-color: #38BDF8;
        box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1);
      }
      
      .add-btn {
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.9rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.3);
      }
      
      .add-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(15, 118, 110, 0.4);
      }
      
      /* Category Section */
      .category-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(15, 118, 110, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.15);
        backdrop-filter: blur(10px);
      }
      
      .category-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.2rem;
        padding-bottom: 0.9rem;
        border-bottom: 2px solid #E0F2FE;
      }
      
      .category-icon {
        font-size: 1.5rem;
      }
      
      .category-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #0F766E;
        flex: 1;
      }
      
      .category-count {
        background: linear-gradient(135deg, #E0F2FE 0%, #38BDF8 100%);
        color: white;
        padding: 0.35rem 0.85rem;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.3);
      }
      
      /* Todo Item */
      .todo-item {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border: 1px solid #E0F2FE;
        border-left: 4px solid #38BDF8;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      
      .todo-item:hover {
        transform: translateX(8px);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.2);
        border-left-color: #0F766E;
      }
      
      .todo-item.completed {
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        border-left: 4px solid #9ca3af;
        opacity: 0.7;
      }
      
      .todo-item.completed .todo-text {
        text-decoration: line-through;
        color: #9ca3af;
      }
      
      .todo-checkbox {
        width: 24px;
        height: 24px;
        cursor: pointer;
        flex-shrink: 0;
        accent-color: #38BDF8;
        transition: transform 0.2s ease;
      }
      
      .todo-checkbox:hover {
        transform: scale(1.15);
      }
      
      .todo-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .todo-text {
        font-size: 1.05rem;
        color: #0F172A;
        line-height: 1.6;
        transition: all 0.3s ease;
        font-weight: 500;
      }
      
      .todo-date {
        font-size: 0.8rem;
        color: white;
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        font-weight: 600;
        padding: 0.35rem 0.8rem;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        width: fit-content;
        box-shadow: 0 2px 10px rgba(56, 189, 248, 0.3);
      }
      
      .delete-btn {
        background: rgba(255, 255, 255, 0.8);
        color: #9ca3af;
        border: 1px solid #E0F2FE;
        border-radius: 10px;
        padding: 0.4rem;
        cursor: pointer;
        font-size: 1.2rem;
        transition: all 0.2s ease;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .delete-btn:hover {
        color: #ef4444;
        background: #fee2e2;
        border-color: #fecaca;
        transform: scale(1.1);
      }
      
      /* Share Button */
      .share-btn {
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1.1rem 2rem;
        font-size: 1.05rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(15, 118, 110, 0.3);
        width: 100%;
        margin-top: 1rem;
      }
      
      .share-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 28px rgba(15, 118, 110, 0.4);
      }
      
      /* Copy Notification */
      .copy-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        padding: 1.1rem 2.2rem;
        border-radius: 20px;
        box-shadow: 0 10px 32px rgba(15, 118, 110, 0.4);
        backdrop-filter: blur(10px);
        display: none;
        animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 1000;
        font-weight: 600;
      }
      
      @keyframes slideInRight {
        from { transform: translateX(120%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      
      /* Empty State */
      .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #64748b;
      }
      
      .empty-state-icon {
        font-size: 4.5rem;
        margin-bottom: 1.2rem;
        opacity: 0.8;
      }
      
      .empty-state-text {
        font-size: 1.15rem;
        color: #94a3b8;
        font-weight: 500;
      }
      
      @media (max-width: 768px) {
        body {
          padding: 1rem;
        }
        
        .hero-header h1 {
          font-size: 1.5rem;
        }
        
        .category-title {
          font-size: 1.1rem;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="hero-header">
        <h1>✨ EchoNote</h1>
      </div>
      
      <button class="add-note-toggle" onclick="toggleAddForm()">
        ✏️ Add New Task
      </button>
      
      <div id="addNoteForm" class="add-note-section">
        <h5>✏️ Create New Task</h5>
        <input type="text" id="newNoteInput" class="add-note-input" placeholder="Enter your task...">
        <input type="date" id="newNoteDate" class="add-note-input">
        <button class="add-btn" onclick="addNote()">+ Add Task</button>
      </div>

      <div id="todoList">
        {% if items %}
          <!-- Important Tasks -->
          {% set important = items | selectattr('importance', 'equalto', 'important') | list %}
          {% if important %}
          <div class="category-section">
            <div class="category-header">
              <span class="category-icon">⭐</span>
              <h3 class="category-title">Important</h3>
              <span class="category-count">{{ important | length }}</span>
            </div>
            {% for item in important %}
              <div class="todo-item {% if item.completed %}completed{% endif %}" data-index="{{ loop.index0 }}">
                <input type="checkbox" class="todo-checkbox" {% if item.completed %}checked{% endif %} onchange="toggleComplete({{ items.index(item) }})">
                <div class="todo-content">
                  <span class="todo-text">{{ item.text }}</span>
                  {% if item.date %}
                  <div class="todo-date">📅 {{ item.date }}{% if item.time %} at {{ item.time }}{% endif %}</div>
                  {% endif %}
                </div>
                <button class="delete-btn" onclick="deleteNote({{ items.index(item) }})">🗑</button>
              </div>
            {% endfor %}
          </div>
          {% endif %}
          
          <!-- Non-Important Tasks -->
          {% set nonimportant = items | selectattr('importance', 'equalto', 'non-important') | list %}
          {% if nonimportant %}
          <div class="category-section">
            <div class="category-header">
              <span class="category-icon">📋</span>
              <h3 class="category-title">Non-Important</h3>
              <span class="category-count">{{ nonimportant | length }}</span>
            </div>
            {% for item in nonimportant %}
              <div class="todo-item {% if item.completed %}completed{% endif %}" data-index="{{ loop.index0 }}">
                <input type="checkbox" class="todo-checkbox" {% if item.completed %}checked{% endif %} onchange="toggleComplete({{ items.index(item) }})">
                <div class="todo-content">
                  <span class="todo-text">{{ item.text }}</span>
                  {% if item.date %}
                  <div class="todo-date">📅 {{ item.date }}{% if item.time %} at {{ item.time }}{% endif %}</div>
                  {% endif %}
                </div>
                <button class="delete-btn" onclick="deleteNote({{ items.index(item) }})">🗑</button>
              </div>
            {% endfor %}
          </div>
          {% endif %}
        {% else %}
          <div class="category-section">
            <div class="empty-state">
              <div class="empty-state-icon">💭</div>
              <div class="empty-state-text">No tasks yet. Send a voice note or add a task above!</div>
            </div>
          </div>
        {% endif %}
      </div>

      <button class="share-btn" onclick="shareLink()">
        📤 Share This List
      </button>
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
          alert('Please enter a task!');
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
        if (!confirm('Delete this task?')) return;

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
            title: '✨ EchoNote',
            text: 'Check out my organized tasks!',
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
          const notification = document.getElementById('notification');
          notification.style.display = 'block';
          setTimeout(() => {
            notification.style.display = 'none';
          }, 3000);
        }).catch(err => {
          console.error('Failed to copy:', err);
          alert('Link: ' + text);
        });
      }
    </script>
  </body>
</html>"""

HOME_HTML = """
<!doctype html>
<html>
  <head>
    <title>EchoNote - AI Voice Planning</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      body {
        background: linear-gradient(135deg, #F9FAFB 0%, #E0F2FE 100%);
        min-height: 100vh;
        padding: 2rem 1rem;
        font-family: 'Inter', -apple-system, sans-serif;
        color: #0F172A;
      }
      
      .container {
        max-width: 900px;
        margin: 0 auto;
      }
      
      /* Header with EchoNote Theme */
      .hero-section {
        background: linear-gradient(135deg, #0F766E 0%, #334155 100%);
        border-radius: 24px;
        padding: 3.5rem 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(15, 118, 110, 0.25);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
      }
      
      .hero-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 40%, rgba(56, 189, 248, 0.15), transparent 70%);
        pointer-events: none;
      }
      
      .hero-section h1 {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.75rem;
        text-shadow: 0 2px 12px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
      }
      
      .hero-section p {
        font-size: 1.25rem;
        color: #E0F2FE;
        font-weight: 400;
        position: relative;
        z-index: 1;
      }
      
      /* Section Container */
      .section-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 24px;
        padding: 2.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(15, 118, 110, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.15);
        backdrop-filter: blur(10px);
      }
      
      .section-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #0F766E;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .section-title::before {
        content: '';
        width: 4px;
        height: 28px;
        background: linear-gradient(180deg, #0F766E 0%, #38BDF8 100%);
        border-radius: 2px;
      }
      
      /* How It Works Steps */
      .steps-container {
        display: grid;
        gap: 1.2rem;
      }
      
      .step-item {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        border-radius: 16px;
        padding: 1.6rem;
        border-left: 4px solid #38BDF8;
        border: 1px solid #E0F2FE;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
      }
      
      .step-item:hover {
        transform: translateX(10px);
        box-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);
        border-left-color: #0F766E;
      }
      
      .step-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.75rem;
      }
      
      .step-number {
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 16px rgba(15, 118, 110, 0.3);
      }
      
      .step-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #0F766E;
      }
      
      .step-description {
        color: #334155;
        font-size: 0.98rem;
        line-height: 1.7;
        margin-left: 3.2rem;
      }
      
      /* Technical Setup Section */
      .tech-box {
        background: linear-gradient(135deg, #E0F2FE 0%, #BFDBFE 100%);
        border-left: 4px solid #38BDF8;
        border-radius: 16px;
        padding: 1.6rem;
        margin-top: 1rem;
        border: 1px solid rgba(56, 189, 248, 0.2);
      }
      
      .tech-box h5 {
        color: #0F766E;
        font-weight: 600;
        margin-bottom: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }
      
      .webhook-url {
        background: #1e293b;
        color: #38BDF8;
        padding: 0.9rem 1.2rem;
        border-radius: 14px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        word-break: break-all;
        margin: 0.75rem 0;
        display: block;
        border: 2px solid #334155;
        font-weight: 500;
      }
      
      /* Features Grid */
      .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.2rem;
        margin-top: 1.2rem;
      }
      
      .feature-item {
        background: linear-gradient(135deg, #F9FAFB 0%, #FFFFFF 100%);
        padding: 1.4rem;
        border-radius: 16px;
        border: 1px solid #E0F2FE;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      
      .feature-item:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 28px rgba(56, 189, 248, 0.2);
        border-color: #38BDF8;
      }
      
      .feature-icon {
        font-size: 2.2rem;
        margin-bottom: 0.6rem;
        display: block;
      }
      
      .feature-title {
        font-weight: 600;
        color: #0F766E;
        margin-bottom: 0.35rem;
        font-size: 1.05rem;
      }
      
      .feature-desc {
        font-size: 0.88rem;
        color: #334155;
        line-height: 1.5;
      }
      
      /* Status Indicator */
      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        background: linear-gradient(135deg, #0F766E 0%, #38BDF8 100%);
        color: white;
        padding: 0.7rem 1.3rem;
        border-radius: 24px;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
      }
      
      .status-dot {
        width: 10px;
        height: 10px;
        background: #38BDF8;
        border-radius: 50%;
        animation: pulse 2s infinite;
        box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7);
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
        50% { opacity: 0.8; transform: scale(1.1); box-shadow: 0 0 0 6px rgba(56, 189, 248, 0); }
      }
      
      /* Calendar Section */
      .calendar-badge {
        background: linear-gradient(135deg, #E0F2FE 0%, #BFDBFE 100%);
        border: 2px solid #38BDF8;
        border-radius: 16px;
        padding: 1.2rem;
        margin-top: 1rem;
        display: flex;
        align-items: center;
        gap: 1.2rem;
      }
      
      .calendar-badge strong {
        color: #0F766E;
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
        <h1>✨ EchoNote</h1>
        <p>Transform your thoughts into organized, prioritized plans</p>
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
              <div class="step-title">🤖 AI Processing</div>
            </div>
            <p class="step-description">
              Our AI transcribes your voice, extracts dates/times, and intelligently classifies tasks as Important or Non-Important.
            </p>
          </div>
          
          <div class="step-item">
            <div class="step-header">
              <div class="step-number">3</div>
              <div class="step-title">⭐ Get Organized</div>
            </div>
            <p class="step-description">
              Receive a beautiful shareable link with tasks auto-categorized by importance and synced to your calendar!
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
            <span class="feature-icon">⭐</span>
            <div class="feature-title">AI Priority</div>
            <div class="feature-desc">Smart classification into Important and Non-Important</div>
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
            <span class="feature-icon">✨</span>
            <div class="feature-title">Modern Design</div>
            <div class="feature-desc">Beautiful, professional teal-gray interface</div>
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

    response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
                                                     messages=[{
                                                         "role":
                                                         "user",
                                                         "content":
                                                         prompt
                                                     }],
                                                     temperature=0,
                                                     max_tokens=50)

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


def classify_task_importance(text):
  """Classify task as important or non-important using AI"""
  try:
    prompt = f"""Classify this task as either "important" or "non-important".

IMPORTANT tasks include:
- Family functions, family events, family gatherings
- Office meetings, work meetings, business meetings
- Medical appointments, doctor visits
- Important deadlines, urgent work
- Celebrations, weddings, parties

NON-IMPORTANT tasks include:
- Shopping, buying items, groceries
- General errands, routine tasks
- Personal reminders, casual notes
- Chores, household tasks

Task: {text}

Respond with ONLY one word: "important" or "non-important"."""

    response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
                                                     messages=[{
                                                         "role":
                                                         "user",
                                                         "content":
                                                         prompt
                                                     }],
                                                     temperature=0,
                                                     max_tokens=10)

    result = response.choices[0].message.content
    if not result:
      return "non-important"

    # Normalize response: remove hyphens and extra spaces
    result = result.strip().lower().replace("-", " ").replace("  ", " ")

    # Check for exact matches
    if result == "important":
      return "important"
    elif "non important" in result or "not important" in result:
      return "non-important"
    elif "important" in result:
      return "important"
    else:
      return "non-important"

  except Exception as e:
    print(f"Error classifying importance: {e}")
    return "non-important"


def get_calendar_service():
  """Get authenticated Google Calendar service (non-blocking)"""
  try:
    import pickle
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    # Only proceed if we already have valid credentials
    if not os.path.exists('token.pickle'):
      print(
          "token.pickle not found. Run /auth endpoint first to authenticate.")
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


def create_calendar_event(task_text,
                          date_str,
                          time_str=None,
                          timezone='America/New_York'):
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
          'description': 'Created from EchoNote'
      }
    else:
      # All-day event - end date must be next day (exclusive)
      end_date = (datetime.strptime(date_str, '%Y-%m-%d') +
                  timedelta(days=1)).strftime('%Y-%m-%d')
      event = {
          'summary': task_text,
          'start': {
              'date': date_str,
          },
          'end': {
              'date': end_date,
          },
          'description': 'Created from EchoNote'
      }

    created_event = service.events().insert(calendarId='primary',
                                            body=event).execute()
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
        twilio.messages.create(from_="whatsapp:+14155238886",
                               to=phone_number,
                               body=message)
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

  headers = {"authorization": api_key}

  print("Uploading audio to AssemblyAI...")
  with open(audio_file_path, "rb") as audio_file:
    upload_response = requests.post("https://api.assemblyai.com/v2/upload",
                                    headers=headers,
                                    data=audio_file,
                                    timeout=60)

    if upload_response.status_code != 200:
      raise Exception(f"Upload failed: {upload_response.text}")

    audio_url = upload_response.json()["upload_url"]
    print(f"Audio uploaded: {audio_url}")

  print("Starting transcription...")
  transcription_payload = {"audio_url": audio_url, "language_code": "en"}

  transcription_response = requests.post(
      "https://api.assemblyai.com/v2/transcript",
      headers=headers,
      json=transcription_payload,
      timeout=60)

  if transcription_response.status_code != 200:
    raise Exception(
        f"Transcription request failed: {transcription_response.text}")

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
    redirect_uri = request.url_root.replace(
        'http://', 'https://').rstrip('/') + '/auth/callback'

    # Create flow with proper redirect URI
    flow = Flow.from_client_secrets_file('credentials.json',
                                         scopes=SCOPES,
                                         redirect_uri=redirect_uri)

    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')

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
    redirect_uri = request.url_root.replace(
        'http://', 'https://').rstrip('/') + '/auth/callback'
    flow = Flow.from_client_secrets_file('credentials.json',
                                         scopes=SCOPES,
                                         state=state,
                                         redirect_uri=redirect_uri)

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
      audio_response = requests.get(url,
                                    auth=(twilio_sid, twilio_token),
                                    timeout=30)
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
      lines = [
          x.strip() for x in text.replace(". ", ".\n").split("\n")
          if x.strip()
      ]
      id = str(uuid.uuid4())[:8]

      # Extract dates, times, and importance from each line
      tasks = []
      for line in lines:
        extracted_date, extracted_time = extract_datetime_from_text(line)
        importance = classify_task_importance(line)
        tasks.append({
            "text": line,
            "completed": False,
            "date": extracted_date,
            "time": extracted_time,
            "importance": importance
        })
        if extracted_date or extracted_time:
          print(
              f"Extracted date='{extracted_date}', time='{extracted_time}' from: {line}"
          )
        print(f"Classified as '{importance}': {line}")

        # Create Google Calendar event if date is present
        if extracted_date:
          calendar_success = create_calendar_event(line, extracted_date,
                                                   extracted_time)
          if calendar_success:
            print(f"✓ Added to Google Calendar: {line}")
          else:
            print(
                f"✗ Could not add to Google Calendar (not configured or error)"
            )

      notes[id] = tasks
      note_owners[id] = who
      link = f"https://{host}/view/{id}"

      print(f"Sending link to {who}")
      try:
        twilio.messages.create(from_="whatsapp:+14155238886",
                               to=who,
                               body=f"Done! Open your list:\n{link}")
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

  importance = classify_task_importance(text)
  notes[id].append({
      "text": text,
      "completed": False,
      "date": date if date else None,
      "time": None,
      "importance": importance
  })
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
