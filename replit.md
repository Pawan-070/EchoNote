# EchoNote - AI-Powered Voice Planning

## Overview
A modern, professional Flask web application that converts WhatsApp voice notes into organized, prioritized to-do lists with AI-powered importance classification, automatic date/time extraction, and Google Calendar integration.

## Features
- **Modern EchoNote Design**: Professional teal-gray color scheme with frosted glass effects and elegant animations
- **Smart Importance Classification**: Tasks automatically classified as "Important" (family functions, office meetings, medical appointments) or "Non-Important" (shopping, errands, chores) using keyword matching
- **Live Clock Widget**: Mini clock displaying current time and date in the top corner
- **Smart Categorization**: Tasks organized into ⭐ Important and 📋 Non-Important sections with visual badges
- **Voice Note Processing**: Receives voice notes via Twilio WhatsApp webhook
- **AI Transcription**: Uses AssemblyAI for accurate English transcription
- **Date/Time Extraction**: AI automatically extracts dates and times from voice notes
- **Google Calendar Sync**: Automatically creates calendar events for scheduled tasks
- **Shareable Links**: Generate unique, beautiful links for each to-do list
- **Interactive UI**: Check off tasks, add new ones, delete, and share with ease

## Tech Stack
- Python 3.11
- Flask (web framework)
- Twilio (WhatsApp integration)
- OpenAI Whisper (audio transcription)
- FFmpeg (audio conversion)

## Environment Variables
The following secrets are configured in Replit Secrets:
- `OPENAI_KEY` - OpenAI API key for Whisper transcription
- `TWILIO_SID` - Twilio Account SID
- `TWILIO_TOKEN` - Twilio Auth Token

## How It Works
1. User sends a WhatsApp voice note to the configured Twilio number
2. Twilio forwards the audio to the `/webhook` endpoint
3. App downloads and transcribes audio using AssemblyAI
4. Each task is classified as "important" or "non-important" using keyword matching
5. AI extracts dates/times from transcription (when OpenAI quota available)
6. Tasks are organized into categorized sections with live clock display
7. Scheduled tasks are automatically added to Google Calendar
8. A unique shareable link with beautiful UI is generated
9. Link is sent back to user via WhatsApp

## Endpoints
- `/` - Home page with app information and webhook URL
- `/webhook` - POST endpoint for receiving Twilio WhatsApp messages
- `/view/<id>` - View a specific to-do list by ID

## Setup Instructions
1. Open WhatsApp on your phone
2. Add this number to your contacts: **+1 (415) 523-8886**
3. Send the activation message: `join though-police`
4. Start sending voice notes with your tasks and plans!

## Current State
- App is running on port 5000
- All API credentials configured
- Ready to receive voice notes via WhatsApp webhook

## Last Updated
November 8, 2025
