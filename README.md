<img width="200" height="200" alt="ChatGPT Image Nov 8, 2025, 01_05_29 PM" src="https://github.com/user-attachments/assets/22cb2747-07ac-4041-a341-93276ea49f9f" /># 🎙️ Voice Plans App

![App Icon](ChatGPT Image Nov 8, 2025, 01_05_29 PM.png…)
)




## 🧠 Overview
**Voice Plans App** is a Flask web application that transforms your **WhatsApp voice notes** into beautiful, shareable **to-do lists**.  
It uses **Twilio** for WhatsApp integration and **AssemblyAI** for AI-powered transcription.

When you send a voice message to your Twilio WhatsApp number, the app automatically:
1. Downloads and transcribes your voice note.
2. Converts the text into a checklist.
3. Sends you a link to view, edit, and share your list.

---

## 🚀 Features
- 🎧 **AI Voice Transcription** — Powered by AssemblyAI  
- 🗒️ **Smart To-Do Generation** — Organizes your spoken notes into structured tasks  
- 🔗 **Shareable Lists** — Get a unique link for each list  
- 📱 **WhatsApp Integration** — Send and receive messages via Twilio  
- 🌈 **Modern UI** — Responsive Bootstrap 5 design with smooth animations  

---

## 🧩 Tech Stack
| Component | Technology |
|------------|-------------|
| Backend | Flask (Python) |
| Messaging | Twilio WhatsApp API |
| Transcription | AssemblyAI API |
| Frontend | HTML, Bootstrap 5, Vanilla JS |
| Environment | Python 3.11+ |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/voice-plans-app.git
cd voice-plans-app
