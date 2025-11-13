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
    YOUTUBE_PLAYLIST_LINK = os.getenv('YOUTUBE_PLAYLIST_LINK', '')

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

    # 72-Hour Window Configuration (Meta WhatsApp Policy)
    WINDOW_72H_SECONDS = 259200  # 72 hours in seconds (3 days)
    WINDOW_24H_SECONDS = 86400  # Legacy: kept for backwards compatibility

    # Respond.io Custom Field Names
    CUSTOM_FIELDS = {
        'FIRST_NAME': 'firstName',
        'CHOSEN_TIMESLOT': 'chosen_timeslot',
        'LAST_72HR_WINDOW': 'last_72hr_window_start',  # Updated to 72hr window
        'LAST_24HR_WINDOW': 'last_24hr_window_start',  # Legacy: kept for backwards compatibility
        'THUMBS_UP': 'thumbs_up_received',
        'MEMBER_STATUS': 'member_status',
        'REMINDER_12H': 'reminder_12h_sent',
        'REMINDER_60MIN': 'reminder_60min_sent',
        'REMINDER_10MIN': 'reminder_10min_sent',
        'NAME_REQUESTED': 'name_requested',
    }

    # Ruul Payment Links
    MEMBERSHIP_LINK = os.getenv('MEMBERSHIP_LINK', '')
    TRIAL_LINK = os.getenv('TRIAL_LINK', '')
    REGISTRATION_LINK = os.getenv('REGISTRATION_LINK', '')

    # Message Templates (Exact from Flow Document)
    @staticmethod
    def get_message_templates():
        return {
            # B1 Z1 - Ask Name
            'B1_Z1': "Hi 🌸 I'm Ineke from InnerJoy! Lovely to connect with you. Can you share your (first) name? Then I'll send your Zoom link 🌈",

            # B1 Z2 - Send Zoom Link + Ask Timeslot
            'B1_Z2': """Hey {name}🌸 Here's your free Zoom link 🌈 {zoom_link}

If this is your first time
using Zoom (its free & safe)
Download Zoom here: https://zoom.us/download

Which day + time fits you best? Choose your letter below 👇

A = Saturday 15:30 o'clock
B = Saturday 20:30 o'clock
C = Sunday 06:30 o'clock
D = Sunday 15:30 o'clock
E = Sunday 20:30 o'clock

All times are in UTC+7 ⏰

Please send us your choice 💫 A, B, C, D or E !""",

            # B1 Z2a1 - Confirm Timeslot
            'B1_Z2A1': """Hey {name} 💖 Great — you're on the list!

🕒 Your chosen time: {timeslot} 🌈

When you'd love to share this moment of Joy with friends or family, here's a little card 🌼

Use it to invite them 💫 and spread the Joy💕""",

            # B1 Z2a2 - Forward Invite Card
            'B1_Z2A2': """Hey lovely! 🌸

I'm joining a 30 minutes free Zoom preview to "Renew your Inner Joy" at {timeslot} 🌈

We dance and do playful creative exercises 🎭 It would be so nice to experience this together 💫

Will you join too? Click this link to sign up 👇
{registration_link}

Warm greetings, {sender_name}""",

            # B1 R1 - Reminder T-12 hours (with thumbs up)
            'B1_R1': """Hello {name} 🌸 Just a gentle reminder — your "Renew your Inner Joy" Zoom preview is coming soon ✨

🕒 Your session starts at {timeslot} (UTC+7)

Question:
Send us a 👍 if you plan to join!

I'm so happy you're joining! Can't wait to see you soon! Ineke – Inner Joy""",

            # B1 R2 - Reminder T-60 minutes (NO thumbs up - removed per new requirements)
            'B1_R2': """Hello {name} 🌸

We're gathering soon for "Renew your Inner Joy"

🕒 Starts at {timeslot} (UTC+7)

Here's your join link 👇
{zoom_link}

I'm so happy you're joining! Can't wait to see you soon! Ineke – Inner Joy""",

            # B1 R3 - Reminder T-10 minutes (NO thumbs up - removed per new requirements)
            'B1_R3': """Hi {name} 🌼

We start in 10 minutes! 30 minutes of live fun exercises to Renew your Inner Joy! ✨

Tap to join now
{zoom_link}

So happy you're coming! Ineke – Inner Joy""",

            # B1 S1 - Sales Offer (T+5 min after slot)
            'B1_S1': """Hey {name} 🌸

How lovely that you just joined our Inner Joy Preview! 💫

Our 3-month membership is just $80 💖

Click here to explore 👇 and join!
Our Membership offer
{membership_link}""",

            # B1 Shake-up 1 - Social Proof (T+20 min)
            'B1_SHAKEUP': """Hey {name} 💫

Inner Joy is thriving! 🌸
Anna, Josephine, Emma and Chloe
just became members 💕

Come join us and create
more Joy in your life 🌈

Here's our Membership Page
{membership_link}""",

            # B1 S2 - Sales Offer 2 (T+2 hrs after slot)
            'B1_S2': """Hi {name} 🌿

Did a smile come up
thinking of the playful
session with Ineke? 😊

Not sure yet?
Try our Fair Trial —
10 days for $12:
{trial_link}

OR…
Go for the full experience 💖
3 months of Inner Joy —
only $80 for full access:
{membership_link}""",

            # B1 S3 - Sales Offer 3 (Sun/Mon morning 9:00 AM)
            'B1_S3': """Hi {name} 🌿

Good morning!
Still thinking about the
playful session with Ineke? 😊

Would you love to feel that joy
more often in your week? 🌸

Here's your link to explore
3 months of Inner Joy —
only $80 for full access:
{membership_link}

OR…
Try our Fair Trial —
10 days for $12:
{trial_link}""",

            # B1 M1 - Member Welcome (Full Membership)
            'B1_M1': """Congratulations {name}! 🌸

Welcome to Renew Your Inner Joy ✨

Here's your Zoom link for this week:
{member_zoom_link}

Join us Mon–Fri 💫
Live 20-min sessions
6:30 / 20:30 (UTC +7)

Missed a session? No worries 💕

All replays + weekend training
are in this week's playlist 🌼
{youtube_playlist_link}

So happy to have you with us 💫
Ineke""",

            # B1 M1a1 - Member Welcome (Fair Trial)
            'B1_M1A1': """Congratulations, {name}! 🌸

Your Fair Trial is active:
{trial_start} → {trial_end}

Here's your Zoom link for this week:
{member_zoom_link}

Join us Mon–Fri 💫
Live 20-min sessions
6:30 / 20:30 (UTC +7)

Missed a session? No worries 💕

All replays + weekend training
are in this week's playlist 🌼
{youtube_playlist_link}

💖 So happy you've joined""",

            # B1 NoSales + NoShow - Combined Friday Follow-up (18:00)
            # This message is sent to BOTH NoSales (attended but didn't buy) AND NoShow (didn't attend)
            # IMPORTANT: Requires Tier 2 approval from Meta (outbound message)
            'B1_NOSALES': """Hello {name} 🌸

I'd love to invite you again 💕

Join me this weekend for another
playful Inner Joy Zoom session 🌈

Come as you are — comfy clothes,
curious heart, and a smile 😊

Choose your time 👇
B = Sat 20:30 A = Sat 15:30
E = Sun 20:30 D = Sun 15:30
C = Sun 06:30 (UTC +7)

Your free Zoom link:
{zoom_link}

Just send your letter 💫 A–E

Or start your 3-month membership 💖
Renew Your Inner Joy — only $80
{membership_link}

Can't wait to see you again 💕""",

            # B1 NoShow - Same as NoSales (combined template)
            'B1_NOSHOW': """Hello {name} 🌸

I'd love to invite you again 💕

Join me this weekend for another
playful Inner Joy Zoom session 🌈

Come as you are — comfy clothes,
curious heart, and a smile 😊

Choose your time 👇
B = Sat 20:30 A = Sat 15:30
E = Sun 20:30 D = Sun 15:30
C = Sun 06:30 (UTC +7)

Your free Zoom link:
{zoom_link}

Just send your letter 💫 A–E

Or start your 3-month membership 💖
Renew Your Inner Joy — only $80
{membership_link}

Can't wait to see you again 💕""",

            # B2 Ra - No Timeslot Preference Reminder
            'B2_RA': """Hey {name}🌸 Here's your free Zoom link 🌈
{zoom_link}

Which day + time fits you best?
Choose your letter below 👇

A = Saturday 15:30 o'clock
B= Saturday 20:30 o'clock
C= Sunday 06:30 o'clock
D= Sunday 15:30 o'clock
E= Sunday 20:30 o'clock

All times are in UTC+7 ⏰

Please send us your choice 💫
A, B, C, D or E !

Or : I already attended""",

            # B2 Rb - No Timeslot Preference Reminder (2nd)
            'B2_RB': """Hey {name}🌸 Here's your free Zoom link
{zoom_link}

Which day + time fits you best?
Choose your letter below 👇

A =Saturday 15:30 o'clock
B= Saturday 20:30 o'clock
C= Sunday 06:30 o'clock
D=Sunday 15:30 o'clock
E= Sunday 20:30 o'clock

All times are in UTC+7 ⏰

Please send us your choice 💫
A, B, C, D or E !

Or : I already attended""",

            # B2 S1 - Sales Offer 1 (Sunday afternoon 16:00)
            'B2_S1': """Hey {name}! 🌸

Is Inner Joy your new goal? 💫

3 Month Membership — $80 💖

Click below to explore 👇
our Membership offer
{membership_link}

It's also our secure payment page 🌈""",

            # B2 S2 - Sales Offer 2 (Monday morning 9:00)
            'B2_S2': """Hi {name} 🌿

Did a smile come up
thinking of the playful
session with Ineke? 😊

Not sure yet?
Try our Fair Trial —
10 days for $12:
{trial_link}

OR…
Go for the full experience 💖
3 months of Inner Joy —
only $80 for full access:
{membership_link}""",
        }

    @staticmethod
    def get_timeslot_display(timeslot: str) -> str:
        """
        Get display text for a timeslot (e.g., 'Saturday 15:30 o'clock')

        Args:
            timeslot: Timeslot letter (A, B, C, D, E)

        Returns:
            Display text for the timeslot
        """
        if timeslot not in Config.TIME_SLOTS:
            return ''

        slot_info = Config.TIME_SLOTS[timeslot]
        day = slot_info['day']
        time_obj = slot_info['time']
        time_str = time_obj.strftime('%H:%M')

        return f"{day} {time_str} o'clock"

    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        required = ['RESPOND_API_KEY', 'GOOGLE_SHEETS_ID']
        missing = [key for key in required if not getattr(Config, key)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True
