# Voice Plans App

![App Icon](WhatsApp Image 2025-11-08 at 22.35.03.jpeg)
)

**Speak once. Get a plan.**  
Transform **WhatsApp voice notes** into **beautiful, shareable to-do lists** — instantly.

---

## Overview

**Voice Plans App** is a Flask web application that turns your **WhatsApp voice notes** into clean, organized, and shareable **to-do lists**.  
It uses **Twilio** for WhatsApp integration and **AssemblyAI** for AI-powered transcription.

When you send a voice message to your Twilio WhatsApp number, the app automatically:

1. Downloads and transcribes your voice note.  
2. Converts the text into a structured checklist.  
3. Sends you a **unique link** to view, edit, and share your list.

---

## Features

- **AI Voice Transcription** — Powered by AssemblyAI  
- **Smart To-Do Generation** — Organizes spoken notes into clear tasks  
- **Shareable Lists** — Get a unique, beautiful link for each list  
- **WhatsApp Integration** — Send voice note → get list back instantly  
- **Modern UI** — Responsive Bootstrap 5 design with smooth animations  

---

## Tech Stack

| Component       | Technology                     |
|-----------------|--------------------------------|
| **Backend**     | Flask (Python)                 |
| **Messaging**   | Twilio WhatsApp API            |
| **Transcription**| AssemblyAI API                 |
| **Frontend**    | HTML, Bootstrap 5, Vanilla JS  |
| **Environment** | Python 3.11+                   |

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/voice-plans-app.git
cd voice-plans-app
