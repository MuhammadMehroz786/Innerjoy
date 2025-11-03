"""
Configuration module for Inner Joy Studio WhatsApp Automation
"""
import os
from datetime import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

    # Respond.io API Configuration
    RESPOND_API_KEY = os.getenv('RESPOND_API_KEY')
    RESPOND_API_URL = os.getenv('RESPOND_API_URL', 'https://api.respond.io/v2')
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

    # Google Sheets Configuration
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Bangkok')

    # Zoom Configuration
    ZOOM_PREVIEW_LINK = os.getenv('ZOOM_PREVIEW_LINK', 'https://us02web.zoom.us/j/82349172983')
    ZOOM_MEMBER_LINK = os.getenv('ZOOM_MEMBER_LINK', '')

    # Pricing Configuration
    MEMBERSHIP_PRICE = int(os.getenv('MEMBERSHIP_PRICE', 80))
    TRIAL_PRICE = int(os.getenv('TRIAL_PRICE', 12))

    # Session Time Slots (UTC+7)
    TIME_SLOTS = {
        'A': {'day': 'Saturday', 'time': time(15, 30), 'day_num': 5},  # Saturday 15:30
        'B': {'day': 'Saturday', 'time': time(20, 30), 'day_num': 5},  # Saturday 20:30
        'C': {'day': 'Sunday', 'time': time(6, 30), 'day_num': 6},     # Sunday 06:30
        'D': {'day': 'Sunday', 'time': time(15, 30), 'day_num': 6},    # Sunday 15:30
        'E': {'day': 'Sunday', 'time': time(20, 30), 'day_num': 6}     # Sunday 20:30
    }

    # Timing Configuration (in minutes)
    TIMESLOT_RESPONSE_TIMEOUT = 120  # 2 hours
    REMINDER_12H = 720  # 12 hours before session
    REMINDER_60MIN = 60  # 1 hour before session
    REMINDER_10MIN = 10  # 10 minutes before session

    # Sales Message Timing (in minutes after session)
    SALES_S1_DELAY = 5
    SALES_SHAKEUP_DELAY = 20
    SALES_S2_DELAY = 120  # 2 hours

    # Tree 2 Sales Timing (in hours from registration)
    TREE2_SALES_1 = 22  # 22 hours
    TREE2_SALES_2 = 23.5  # 23.5 hours

    # 24-Hour Window Configuration
    WINDOW_24H_SECONDS = 86400  # 24 hours in seconds

    # Respond.io Custom Field Names
    CUSTOM_FIELDS = {
        'FIRST_NAME': 'firstName',
        'CHOSEN_TIMESLOT': 'chosen_timeslot',
        'LAST_24HR_WINDOW': 'last_24hr_window_start',
        'THUMBS_UP': 'thumbs_up_received',
        'MEMBER_STATUS': 'member_status',
        'REMINDER_12H': 'reminder_12h_sent',
        'REMINDER_60MIN': 'reminder_60min_sent',
        'REMINDER_10MIN': 'reminder_10min_sent',
        'NAME_REQUESTED': 'name_requested',
    }

    # Message Templates
    @staticmethod
    def get_message_templates():
        return {
            'ASK_NAME': "Hi 🌸 I'm Ineke from InnerJoy! Lovely to connect with you. Can you share your (first) name? Then I'll send your Zoom link 🌈",

            'SEND_ZOOM_LINK': """Wonderful to meet you, {name}! 🤗

Here's your personal Zoom link for our free 30-minute preview session:
🔗 {zoom_link}

I have sessions at these times (Bangkok time):

A) Saturday 15:30
B) Saturday 20:30
C) Sunday 06:30
D) Sunday 15:30
E) Sunday 20:30

Which time works best for you? Just reply with the letter (A, B, C, D, or E) 🌟""",

            'CONFIRM_TIMESLOT': """Perfect! ✨ I've saved your spot for {day} at {time} (Bangkok time).

Here's your Zoom link:
🔗 {zoom_link}

I'll send you a reminder before the session. Looking forward to seeing you there! 🌈

If anything changes, just let me know 💛""",

            'REMINDER_12H_WITH_THUMBS': """Hi {name}! 👋

Just a friendly reminder - your Inner Joy preview session is tomorrow at {time} (Bangkok time).

🔗 Zoom link: {zoom_link}

Send a 👍 if you're all set, or let me know if you have any questions! 🌸""",

            'REMINDER_12H_NO_THUMBS': """Hi {name}! 👋

Just a friendly reminder - your Inner Joy preview session is tomorrow at {time} (Bangkok time).

🔗 Zoom link: {zoom_link}

Looking forward to seeing you there! 🌸""",

            'REMINDER_60MIN': """Hi {name}! ⏰

Your session starts in 1 hour at {time}!

🔗 Join here: {zoom_link}

See you soon! 💛""",

            'REMINDER_10MIN': """Hi {name}! 🚀

Your session starts in 10 minutes!

🔗 Join now: {zoom_link}

I'm ready when you are! ✨""",

            'SALES_S1': """Hi {name}! 🌸

I hope you enjoyed our preview session! I loved having you there.

I'm opening up spots for my 3-month Inner Joy membership - just $80 for 12 weeks of weekly group sessions, community support, and personal growth tools.

Would you like to join us? 💛""",

            'SALES_SHAKEUP': """By the way {name}, I should mention - last month, 8 out of 10 members told me they finally feel like they're making real progress with their inner peace journey.

The difference? Consistency. Weekly sessions, supportive community, accountability.

Just wanted you to know what's possible 🌈""",

            'SALES_S2': """Hi {name}! 🌟

I have two options for you:

1️⃣ Trial: $12 for 10 days - try 2 full sessions with the group
2️⃣ Membership: $80 for 3 months - commit to your transformation

Which one feels right for you? Or do you have questions I can answer? 💫""",

            'TREE2_SALES_1': """Hi {name}! 👋

I noticed you haven't picked a session time yet. No pressure at all!

But I want you to know - the spot is still yours whenever you're ready. The sessions are free, casual, and many people say it's the best 30 minutes of their weekend 🌸

Want to give it a try? Just pick a time:

A) Saturday 15:30
B) Saturday 20:30
C) Sunday 06:30
D) Sunday 15:30
E) Sunday 20:30

🔗 {zoom_link}""",

            'TREE2_SALES_2': """Last call, {name}! 🌟

I'm here if you change your mind. Sometimes the best things happen when we say yes to something new.

If you'd like to join any session this weekend, just let me know. I'd love to see you there! 💛

Or if you prefer, I can send you some free resources about inner peace and mindfulness? 🌈""",

            'NOSHOW_REINVITE': """Hi {name}! 🌸

I missed you at last week's session! Life gets busy, I totally understand.

Would you like to try again this weekend? I have new times available:

A) Saturday 15:30
B) Saturday 20:30
C) Sunday 06:30
D) Sunday 15:30
E) Sunday 20:30

🔗 {zoom_link}

Let me know if any of these work better for you! 💛""",

            'NOSALES_REINVITE': """Hi {name}! 👋

It was wonderful having you in the session last week! I'm glad you got to experience the Inner Joy practice.

I have more sessions this weekend if you'd like to join again (they're always free for preview):

A) Saturday 15:30
B) Saturday 20:30
C) Sunday 06:30
D) Sunday 15:30
E) Sunday 20:30

Or if you're ready, I can share details about joining as a member! 🌟

What feels right for you? 💛""",

            'PAYMENT_RECEIVED': """Thank you so much, {name}! 🎉

I've received your payment. Welcome to the Inner Joy family! 💛

Here's your member Zoom link for weekly sessions:
🔗 {member_zoom_link}

Sessions are every [day/time]. I'll send you reminders before each one.

I'm so excited to support your journey! 🌈✨""",
        }

    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        required = ['RESPOND_API_KEY', 'GOOGLE_SHEETS_ID']
        missing = [key for key in required if not getattr(Config, key)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True
