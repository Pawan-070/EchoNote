# Google Calendar Integration Setup Guide

## Overview
Your Voice Plans App now automatically adds tasks to Google Calendar when you mention dates and times in your voice notes!

## Setup Instructions

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it "Voice Plans Calendar" (or any name you prefer)
4. Click **Create**

### Step 2: Enable Google Calendar API
1. In your new project, go to **APIs & Services** → **Library**
2. Search for **"Google Calendar API"**
3. Click on it and press **Enable**

### Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have Google Workspace)
3. Click **Create**
4. Fill in the required fields:
   - **App name**: Voice Plans App
   - **User support email**: Your email
   - **Developer contact email**: Your email
5. Click **Save and Continue**
6. On the "Scopes" page, click **Add or Remove Scopes**
7. Search for `calendar` and select:
   - `https://www.googleapis.com/auth/calendar` (for full access)
8. Click **Update** → **Save and Continue**
9. Add your email as a test user
10. Click **Save and Continue** → **Back to Dashboard**

### Step 4: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as application type
4. Name it "Voice Plans Desktop"
5. Click **Create**
6. Click **Download JSON** (the download icon)
7. **Rename the downloaded file to `credentials.json`**
8. **Upload it to this Replit project** (drag and drop into the file browser)

### Step 5: First-Time Authentication
1. Run your app (it should already be running)
2. When you send your first voice note with a date/time, the authentication will trigger
3. Look at the console logs - you'll see a URL
4. Open that URL in your browser
5. Sign in with your Google account
6. Grant the permissions
7. You'll be redirected - the authentication is complete!

### Step 6: Test It!
Send a WhatsApp voice note like:
- "Meeting with John tomorrow at 3pm"
- "Doctor appointment Friday at 2:30pm"
- "Buy groceries on December 15th"

The task will:
1. ✅ Appear in your Voice Plans list
2. ✅ Be added to your Google Calendar automatically
3. ✅ Show the date/time in your notes

## How It Works

### Date & Time Detection
The app uses AI to understand natural language dates and times:
- **"tomorrow at 3pm"** → Calculates tomorrow's date + 15:00
- **"Friday 2:30pm"** → Next Friday + 14:30
- **"December 25th"** → 2025-12-25 (all-day event)
- **"on the 15th at 5pm"** → Current month, 15th + 17:00

### Calendar Events
- **With time**: Creates 1-hour event at specified time
- **Without time**: Creates all-day event
- **Description**: All events include "Created from Voice Plans App"
- **Calendar**: Events are added to your primary Google Calendar

## Security Notes
- ✅ Your `credentials.json` and `token.pickle` files are in `.gitignore`
- ✅ These files will NOT be committed to version control
- ✅ Your credentials stay private and secure
- ⚠️ Never share these files publicly

## Troubleshooting

### "credentials.json not found"
- Make sure you uploaded the file to the root directory of this project
- Check the filename is exactly `credentials.json`

### Authentication window doesn't open
- Check the console logs for the authentication URL
- Copy and paste it into your browser manually

### Events not appearing in calendar
- Check console logs for error messages
- Verify you completed the OAuth consent screen setup
- Make sure you granted calendar permissions
- Try re-authenticating by deleting `token.pickle` and restarting the app

### Calendar integration disabled
- This happens when `credentials.json` is missing
- The app will still work normally, just without calendar sync
- Upload `credentials.json` and restart to enable

## Optional: Disable Calendar Integration
If you don't want calendar integration:
1. Simply don't upload `credentials.json`
2. The app will work perfectly without it
3. Tasks will still show dates/times in your notes

---

**Need Help?**
Check the [Google Calendar API Documentation](https://developers.google.com/workspace/calendar/api/quickstart/python) for more details.
