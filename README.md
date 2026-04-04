# Altea Automatic Booking System

Automatically books gym classes at Altea (myaltea.app) when you receive a waitlist notification email.

When someone cancels and a spot opens up, Altea sends you an email with a "Book Now" link. This system monitors your Gmail inbox **every second** and instantly attempts to book the class before it fills up again (typically within 10 seconds).

**This is designed to run continuously on a dedicated machine** (e.g. an old laptop, a Raspberry Pi, or a home server) so it can monitor your email 24/7 and book classes the moment a spot opens up.

---

## ⚡ Quick Start Guide

### Step 1: Install Dependencies (5 minutes)

```bash
cd altea-automatic-booking

# Install Python packages
pip install -r requirements.txt

# Install Chromium for Playwright (fallback browser)
python3 -m playwright install chromium
```

The bot uses your **locally installed browser** (Brave or Chrome) for booking, which avoids bot detection. Make sure you have one of these installed:
- **Brave** (recommended): The bot looks for `/usr/bin/brave-browser` by default
- **Chrome**: Update the `executable_path` in `src/booking_bot.py` to your Chrome path (e.g. `/usr/bin/google-chrome`)

> **Ubuntu/Debian users:** `pip install` may fail with an "externally-managed-environment" error. Use a virtual environment instead:
> ```bash
> python3 -m venv venv
> source venv/bin/activate  # run this each time you open a new terminal
> pip install -r requirements.txt
> python3 -m playwright install chromium
> ```

### Step 2: Set Up Gmail App Password (5 minutes)

The system needs to read your Gmail to detect waitlist notifications.

**IMPORTANT**: You need an App Password (not your regular Gmail password):

1. Go to: **https://myaccount.google.com/apppasswords**
2. Sign in to your Google account
3. You'll be asked to enable **2-Step Verification** if you haven't already (required!)
4. Once 2-Step is enabled, go back to App Passwords: **https://myaccount.google.com/apppasswords**
5. App name: **"Altea Booking"**
6. Click **Generate**
7. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
8. Save it for the next step

### Step 3: Create Configuration File (2 minutes)

```bash
# Copy the example file
cp .env.example .env

# Edit it with your favorite editor
nano .env
# or
vim .env
# or open it in VS Code, etc.
```

Fill in these values in `.env`:

```bash
# Your Gmail address
EMAIL_ADDRESS=your-email@gmail.com

# The 16-character App Password from Step 2 (NOT your regular Gmail password!)
EMAIL_PASSWORD=abcd efgh ijkl mnop

# Altea website
ALTEA_URL=https://myaltea.app/booking/

# Email filtering - Altea sends emails from this address
EMAIL_FROM_FILTER=no-reply@myaltea.club

# Altea emails say this when a spot opens
EMAIL_SUBJECT_FILTER=A Spot Has Opened Up

# Retry settings - try 2 times before giving up
MAX_RETRIES=2

# Check email every 1 second (fast!)
POLL_INTERVAL_SECONDS=1

# Send you email notifications about booking attempts
SEND_NOTIFICATIONS=true
NOTIFICATION_EMAIL=your-email@gmail.com
```

**Save the file** (Ctrl+O, Enter, Ctrl+X in nano)

### Step 4: Test Gmail Connection (2 minutes)

Test that the email monitoring works:

```bash
python3 test_email.py
```

You should see:
```
✓ Connected to Gmail successfully!
✓ Found X recent Altea email(s)!
  ✓ Class URL: https://myaltea.app/booking/evt_...
  ✓ Class Name: Hot Pilates Power - Level 3
```

If you get errors:
- **"Failed to connect"**: Check your `EMAIL_ADDRESS` and `EMAIL_PASSWORD` in `.env`
- **"No emails found"**: You might not have any Altea emails yet - that's okay, continue to next step

### Step 5: Set Up Altea Login Session (3 minutes)

The booking bot needs to be logged in to Altea. Run this once to save your login:

```bash
python3 test_login.py
```

This will:
1. Open a browser window showing myaltea.app
2. Wait for you to log in manually
3. Save your login session for future use

**In the browser window:**
1. Click the login button
2. Enter your Altea credentials (email & password)
3. Complete login
4. Once you see your Altea homepage/workouts, go back to terminal
5. Press Enter

Your login session is now saved! The bot will stay logged in.

### Step 6: Run the Booking System! 🎉

```bash
python3 src/main.py
```

You should see:
```
🏋️  ALTEA AUTO-BOOKING SYSTEM STARTING
Email: your-email@gmail.com
Altea URL: https://myaltea.app/booking/
Poll interval: 1 second(s)
Max retries: 2

🔍 Starting email monitor (checking every 1s)
   Looking for emails from: no-reply@myaltea.club
   With subject containing: A Spot Has Opened Up
```

**The system is now running!**

It will:
- ✅ Check your Gmail every second
- ✅ Detect Altea waitlist notifications
- ✅ Extract the class booking URL from the email
- ✅ Open the class page in a browser
- ✅ Click "Book Now" as soon as the button becomes enabled
- ✅ Retry up to 2 times if booking fails
- ✅ Send you an email notification of the result
- ✅ Continue monitoring for the next notification

**Leave it running continuously!** This works best on a dedicated machine (old laptop, Raspberry Pi, home server) that stays on 24/7. Spots can open up at any time — the bot needs to be running to catch them.

To stop: Press `Ctrl+C`

---

## 🖥️ Running Continuously

### Option 1: Simple Background (Linux/Mac)

```bash
# Run in background
nohup python3 src/main.py > altea_booking.log 2>&1 &

# Check if it's running
ps aux | grep main.py

# View logs in real-time
tail -f altea_booking.log

# Stop it
pkill -f main.py
```

### Option 2: Keep Running on macOS (using screen)

```bash
# Start a screen session
screen -S altea

# Run the booking system
python3 src/main.py

# Detach from screen (keep it running): Press Ctrl+A, then D

# Re-attach later to check on it
screen -r altea

# Stop it: Ctrl+C in the screen session
```

### Option 3: systemd Service (Linux - Auto-restart)

Create `/etc/systemd/system/altea-booking.service`:

```ini
[Unit]
Description=Altea Auto-Booking Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/altea-automatic-booking
ExecStart=/usr/bin/python3 /home/your-username/altea-automatic-booking/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable altea-booking
sudo systemctl start altea-booking

# Check status
sudo systemctl status altea-booking

# View logs
journalctl -u altea-booking -f
```

### Option 4: Windows Task Scheduler

1. Create `run_booking.bat`:
```batch
@echo off
cd C:\path\to\altea-automatic-booking
python src\main.py
```

2. Open **Task Scheduler**
3. **Create Basic Task** → Name: "Altea Auto-Booking"
4. **Trigger**: "When I log on"
5. **Action**: Start a program → Select your `run_booking.bat` file
6. ✅ Done! It will start automatically when you log in

---

## 📧 How It Works

### The Email

When a spot opens in a class you're waitlisted for, Altea sends an email like this:

```
From: Altea <no-reply@myaltea.club>
Subject: A Spot Has Opened Up in Hot Pilates Power - Level 3!

[Book Now!] ← This button has a link to the class
```

### The Booking Flow

1. **Email Detected** (within 1 second of arrival)
   - Script checks Gmail every second
   - Finds email from `no-reply@myaltea.club` with "A Spot Has Opened Up" in subject

2. **Extract Class URL** (< 0.5 seconds)
   - Parses the email HTML
   - Finds the booking link (e.g., `https://myaltea.app/booking/evt_xxx_timestamp`)

3. **Navigate to Class** (1-2 seconds)
   - Opens the class page in browser
   - Uses saved login session (no re-login needed)

4. **Wait for Button** (instant when spot is available)
   - The "Book Now" button is greyed out when full
   - Becomes clickable when spot is available
   - Bot clicks it immediately

5. **Confirm Booking** (< 1 second)
   - Clicks the "Confirm Booking" button (required to complete the booking)
   - Takes screenshot of result

**Total Time: ~2-5 seconds from email arrival to booking attempt** ⚡

---

## 🔧 Configuration Options

All settings are in `.env`:

### Email Settings

```bash
# Your Gmail credentials
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # App Password, not regular password!

# Gmail server (don't change these)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
```

### Altea Settings

```bash
# Altea website URL
ALTEA_URL=https://myaltea.app/booking/

# Email filtering - what emails to look for
EMAIL_FROM_FILTER=no-reply@myaltea.club          # Emails from this sender
EMAIL_SUBJECT_FILTER=A Spot Has Opened Up        # With this phrase in subject
```

### Booking Behavior

```bash
# How many times to retry booking if first attempt fails
MAX_RETRIES=2

# How often to check for new emails (in seconds)
# 1 = check every second (recommended for speed)
# 2 = check every 2 seconds (lighter on Gmail)
POLL_INTERVAL_SECONDS=1
```

### Notifications

```bash
# Send you email updates?
SEND_NOTIFICATIONS=true

# Where to send notifications
NOTIFICATION_EMAIL=your-email@gmail.com
```

---

## 📝 Logs and Screenshots

### Log Files

Logs are saved in `logs/` directory:
- **Daily log files**: `logs/altea_booking_YYYYMMDD.log`
- **Auto-rotated**: Kept for 30 days

View live logs:
```bash
tail -f logs/altea_booking_*.log
```

### Screenshots

The bot automatically takes screenshots:
- `logs/booking_success_TIMESTAMP.png` - When booking succeeds
- `logs/booking_error_TIMESTAMP.png` - When booking fails
- `logs/no_button_TIMESTAMP.png` - When "Book Now" button not found

These help you understand what happened!

---

## 🐛 Troubleshooting

### "Failed to connect to email"

**Cause**: Gmail login issue

**Solutions**:
- ✅ Check `EMAIL_ADDRESS` is correct in `.env`
- ✅ Check `EMAIL_PASSWORD` is your **App Password** (16 characters, not your regular password)
- ✅ Enable 2-Step Verification: https://myaccount.google.com/security
- ✅ Create App Password: https://myaccount.google.com/apppasswords

### "No emails found from 'myaltea.club'"

**Cause**: No Altea emails in your inbox yet, or wrong filter

**Solutions**:
- ✅ Check your Gmail for Altea emails
- ✅ Look at the "From" address in those emails
- ✅ Update `EMAIL_FROM_FILTER` in `.env` if different
- ✅ Run `python test_email.py` to verify

### "Could not find 'Book Now' button"

**Cause**: Page didn't load, or button has different text

**Solutions**:
- ✅ Check the screenshot in `logs/no_button_TIMESTAMP.png` to see what the page looked like
- ✅ Make sure your login session is valid (run `python test_login.py` again)
- ✅ The class URL from the email might be invalid

### "Login required!"

**Cause**: Browser session expired

**Solution**:
- ✅ Run `python test_login.py` again to save a fresh login session

### "Button still disabled after 10 seconds"

**Cause**: Class is still full (no spot actually available)

**Possible reasons**:
- Someone else booked it faster
- The email was a false alarm
- The spot was reserved by someone already

**What happens**:
- Bot will retry (up to `MAX_RETRIES` times)
- Then give up and wait for the next email

### Browser doesn't start

**Cause**: Playwright browser not installed

**Solution**:
```bash
python3 -m playwright install firefox
```

**On Linux**, you might also need:
```bash
sudo apt-get install -y libglib2.0-0 libnss3 libatk1.0-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

---

## 🧪 Testing

### Test Email Connection

```bash
python3 test_email.py
```

Verifies:
- ✅ Gmail login works
- ✅ Can find Altea emails
- ✅ Can extract class URLs from emails

### Test Login Session

```bash
python3 test_login.py
```

Verifies:
- ✅ Browser opens
- ✅ Can log in to Altea
- ✅ Session is saved

### Test Individual Components

```bash
# Test configuration
python3 src/config.py

# Test email monitor (will start monitoring - Ctrl+C to stop)
python3 src/email_monitor.py

# Test booking bot (will open browser)
python3 src/booking_bot.py
```

---

## 🔒 Security

- **Never commit your `.env` file!** (it's in `.gitignore`)
- **Use App Passwords** instead of your main Gmail password
- **Browser session** is saved locally in `playwright-state/firefox_profile/`
- **Logs might contain** email content - keep `logs/` directory private

---

## 📂 Project Structure

```
altea-automatic-booking/
├── src/
│   ├── main.py              # Main orchestrator - run this!
│   ├── config.py            # Configuration loader
│   ├── email_monitor.py     # Gmail monitoring (IMAP)
│   ├── booking_bot.py       # Browser automation (Playwright)
│   └── notifier.py          # Email notifications
├── logs/                    # Log files & screenshots (auto-created)
├── playwright-state/        # Saved browser sessions (auto-created)
├── test_email.py            # Test script for Gmail connection
├── test_login.py            # Test script for Altea login
├── .env.example             # Configuration template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## ❓ FAQ

### How fast does it book?

**~2-5 seconds** from email arrival to booking attempt. This includes:
- Email detection (1 second polling)
- Extracting class URL (< 0.5 seconds)
- Opening class page (1-2 seconds)
- Clicking "Book Now" (instant)

### Will it work if I'm not at my computer?

**Yes!** That's the whole point. Run it in the background (see "Running as Background Service" above), and it will keep monitoring 24/7.

### Does it book ALL classes?

**No, only classes you're waitlisted for.** When Altea sends you a "spot available" email, the bot books that specific class.

### What if multiple spots open at once?

The bot processes one email at a time. If multiple emails arrive, it will handle them sequentially (one after another).

### Can I use this for multiple Altea locations?

Yes! The system works with any Altea gym (myaltea.app). The email and website structure is the same.

### Will Altea ban me for using this?

This automation:
- ✅ Uses a real browser (not a script making fake requests)
- ✅ Books only when you receive a legitimate waitlist notification
- ✅ Respects the website (doesn't overload it)
- ✅ Is for personal use only

It's no different than clicking "Book Now" yourself really fast. However, check Altea's Terms of Service if you're concerned.

### What if booking fails?

The bot will:
1. Retry up to `MAX_RETRIES` times (default: 2)
2. Send you an email notification with the error
3. Take a screenshot for debugging
4. Continue monitoring for the next waitlist notification

### Can I book multiple spots for different people?

The bot books using your logged-in Altea account. If Altea allows you to book multiple spots on your account, then yes. Otherwise, it will book one spot (for you).

---

## 🎯 Tips for Success

1. **Join waitlists early** - The more waitlists you're on, the more chances to get in

2. **Keep the bot running 24/7** - Spots can open up any time

3. **Check logs regularly** - Make sure it's still running and connected

4. **Test monthly** - Run `python3 test_login.py` every month to refresh your session

5. **Monitor your email** - The bot sends notifications, so you'll know if it booked for you

6. **Have backup** - Keep your phone handy too, in case the bot has issues

---

## 🤝 Support

If you encounter issues:

1. **Check logs**: `tail -f logs/altea_booking_*.log`
2. **Check screenshots**: Look in `logs/` for error screenshots
3. **Run tests**:
   - `python3 test_email.py` - Test Gmail connection
   - `python3 test_login.py` - Test Altea login
   - `python3 src/config.py` - Test configuration
4. **Enable debug logging**: In `src/main.py` line 40, change `"INFO"` to `"DEBUG"`

---

## 🚀 Next Steps

You're all set! Here's what to do now:

1. ✅ Join waitlists for classes you want
2. ✅ Run `python3 src/main.py` and leave it running
3. ✅ Wait for waitlist notifications
4. ✅ Check your email for booking success notifications
5. ✅ Enjoy your classes! 🏋️

**Happy booking!** 🎉
