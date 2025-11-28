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
    RESPOND_CHANNEL_ID = int(os.getenv('RESPOND_CHANNEL_ID', 431307))  # WhatsApp Business channel ID (must be integer)
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

    # Google Sheets Configuration
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

    # Timezone Configuration (UTC+8 for Singapore & Hong Kong)
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Singapore')

    # Zoom Configuration
    ZOOM_PREVIEW_LINK = os.getenv('ZOOM_PREVIEW_LINK', 'https://us02web.zoom.us/j/82349172983')
    ZOOM_MEMBER_LINK = os.getenv('ZOOM_MEMBER_LINK', '')
    YOUTUBE_PLAYLIST_LINK = os.getenv('YOUTUBE_PLAYLIST_LINK', '')

    # Pricing Configuration
    MEMBERSHIP_PRICE = int(os.getenv('MEMBERSHIP_PRICE', 80))
    TRIAL_PRICE = int(os.getenv('TRIAL_PRICE', 12))

    # Session Time Slots (UTC+8 - Singapore & Hong Kong)
    TIME_SLOTS = {
        'A': {'day': 'Saturday', 'time': time(15, 30), 'day_num': 5, 'is_walkin': False},  # Saturday 15:30
        'B': {'day': 'Saturday', 'time': time(19, 30), 'day_num': 5, 'is_walkin': True, 'end_time': time(21, 30)},  # Saturday 19:30-21:30 (walk-in)
        'C': {'day': 'Sunday', 'time': time(15, 30), 'day_num': 6, 'is_walkin': False},    # Sunday 15:30
        'D': {'day': 'Sunday', 'time': time(19, 30), 'day_num': 6, 'is_walkin': True, 'end_time': time(21, 30)}     # Sunday 19:30-21:30 (walk-in)
    }

    # Timing Configuration (in minutes)
    TIMESLOT_RESPONSE_TIMEOUT = 120  # 2 hours - triggers Tree 2
    REMINDER_12H = 720  # 12 hours before session
    REMINDER_60MIN = 60  # 1 hour before session
    REMINDER_10MIN = 10  # 10 minutes before session

    # Sales Message Timing (Tree 1 - in minutes after session end)
    SALES_S1_DELAY = 5  # T+5 min after slot
    SALES_SHAKEUP_DELAY = 20  # T+20 min after slot
    SALES_S2_DELAY = 120  # T+2 hours after slot
    SALES_S3_NEXT_MORNING = True  # T+next morning (Sun/Mon) at 9:00 AM

    # Tree 2 Timing (immediate when no timeslot chosen in 2h)
    TREE2_RA_IMMEDIATE = True  # Immediate when entering Tree 2
    TREE2_RB_DELAY = 120  # 2 hours after B2 Ra (in minutes)
    TREE2_S1_DAY = 0  # Sunday (0=Sunday, 1=Monday)
    TREE2_S1_TIME = time(16, 0)  # 16:00 (4 PM)
    TREE2_S2_DAY = 1  # Monday
    TREE2_S2_TIME = time(9, 0)  # 9:00 AM

    # NoShow/NoSales Re-invite Timing
    FRIDAY_REINVITE_TIME = time(18, 0)  # Friday 18:00
    NOSALES_NOSHOW_HOLD_WEEKS = 6  # Hold for 5-6 weeks (waiting for Tier 2 approval)

    # Contact Source Types
    SOURCE_FACEBOOK_ADS = 'facebook_ads'  # 72-hour window
    SOURCE_WEBSITE = 'website'  # 24-hour window

    # Website Detection Trigger Message
    # This is the pre-filled message that website visitors will send via Click-to-WhatsApp
    # If the first message contains this phrase, contact is tagged as 'website' (24h window)
    # Otherwise, contact is tagged as 'facebook_ads' (72h window)
    # Using a natural phrase that fits into a normal greeting
    WEBSITE_TRIGGER_MESSAGE = os.getenv('WEBSITE_TRIGGER_MESSAGE', 'free Zoom preview link')

    # Window Configuration (Meta WhatsApp Policy)
    WINDOW_72H_SECONDS = 259200  # 72 hours in seconds (3 days) - for Facebook Ads
    WINDOW_24H_SECONDS = 86400   # 24 hours in seconds - for Website/FB Page

    # Respond.io Custom Field Names
    CUSTOM_FIELDS = {
        'FIRST_NAME': 'firstName',
        'CHOSEN_TIMESLOT': 'chosen_timeslot',
        'LAST_72HR_WINDOW': 'last_72hr_window_start',  # For Facebook Ads contacts
        'LAST_24HR_WINDOW': 'last_24hr_window_start',  # For Website/FB Page contacts
        'CONTACT_SOURCE': 'contact_source',  # 'facebook_ads' or 'website'
        'THUMBS_UP': 'thumbs_up_received',
        'MEMBER_STATUS': 'member_status',
        'REMINDER_12H': 'reminder_12h_sent',
        'REMINDER_60MIN': 'reminder_60min_sent',
        'REMINDER_10MIN': 'reminder_10min_sent',
        'NAME_REQUESTED': 'name_requested',
    }

    # Payment Links (innerjoy.live - processed by LAILAOLAB ICT/PhaPay)
    MEMBERSHIP_LINK = os.getenv('MEMBERSHIP_LINK', 'https://innerjoy.live/membership/')
    TRIAL_LINK = os.getenv('TRIAL_LINK', 'https://innerjoy.live/fair-trial/')
    REGISTRATION_LINK = os.getenv('REGISTRATION_LINK', 'https://innerjoy.live/')
    ZOOM_DOWNLOAD_LINK = 'https://zoom.us/download'

    # Message Templates (Exact from Flow Document)
    @staticmethod
    def get_message_templates():
        return {
            # ========== 72-HOUR WINDOW MESSAGES (Facebook Ads Contacts) ==========

            # B1 Z1 - Ask Name (72h flow)
            'B1_Z1': "Hi 🌸 I'm Ineke from InnerJoy! Lovely to connect with you. Can you share your (first) name? Then I'll send your Zoom link 🌈",

            # ========== 24-HOUR WINDOW MESSAGES (Website/FB Page Contacts) ==========

            # B1 Z1 - Ask Name (24h flow - combined with timeslot info)
            'B1_Z1_24H': """Hi 🌸 I'm Ineke from InnerJoy!
Lovely to connect with you.
Please share your first name and
I'll send your free Zoom preview link 🌈

These are our free
Renew Your Inner Joy
Zoom preview sessions
this weekend (UTC+8):

A — Sat 15:30 (30 min)
B — Sat 19:30–21:30 (walk-in)
C — Sun 15:30 (30 min)
D — Sun 19:30–21:30 (walk-in)

Please share your first name and
I'll send your free Zoom preview link 🌈""",

            # B1 Z2 - Send Zoom Link + Ask Timeslot
            'B1_Z2': """Hey {name} 🌸

Here is your Zoom link 🌈

{zoom_link}



If Zoom is new for you,

download it here:

{zoom_download_link}



We host free walk-in

preview sessions this

weekend for SG & HK (UTC+8).

These are Renew Your Inner Joy

preview sessions ✨

Join 20–30 mins anytime

in this timeframe to feel the uplifting energy 💛



Choose your option 👇



A = Sat 15:30

B = Sat 19:30–21:30 (walk-in)

C = Sun 15:30

D = Sun 19:30–21:30 (walk-in)



All times in UTC+8 ⏰

Reply A, B, C or D 💫""",

            # B1 Z2a1 - Confirm Timeslot
            'B1_Z2A1': """Hey {name} 💖
Great — you're on the list!
🕒 Your chosen time:
{timeslot} 🌈

When you'd love to share
this moment of Joy
with friends or family,
here's a little card 🌼

Use it to invite them 💫
and spread the Joy💕""",

            # B1 Z2a2 - Forward Invite Card
            'B1_Z2A2': """Hey lovely! 🌸

I'm joining a 30 minutes free
Zoom preview to "Renew your
Inner Joy" at {timeslot} 🌈

We dance and do playful
creative exercises 🎭
It would be so nice
to experience this together 💫

Will you join too?
Click this link to sign up 👇
{registration_link}

Warm greetings,
{sender_name}""",

            # B1 R1 - Reminder T-12 hours
            'B1_R1': """Hello {name} 🌸
Just a gentle reminder —
your "Renew your Inner Joy"
Zoom preview is coming soon ✨

🕒 Your session starts at
{timeslot} (UTC+8)

I'm so happy you're joining!
Can't wait to see you soon!
Ineke – Inner Joy""",

            # B1 R2 - Reminder T-60 minutes
            'B1_R2': """Hello {name} 🌸

We're gathering soon for
"Renew your Inner Joy"

🕒 Starts at {timeslot} (UTC+8)

Here's your join link 👇
{zoom_link}

I'm so happy you're joining!
Can't wait to see you soon!
Ineke – Inner Joy""",

            # B1 R3 - Reminder T-10 minutes
            'B1_R3': """Hi {name} 🌼

We start in 10 minutes!
30 minutes of live fun
exercises to Renew
your Inner Joy! ✨

Tap to join now
{zoom_link}


So happy you're coming!
Ineke – Inner Joy""",

            # B1 S1 - Sales Offer (T+5 min after slot)
            'B1_S1': """Hey {name} 🌸

How lovely that you just
joined our Inner Joy Preview! 💫

Our 3-month membership
is just $80 💖

Click here to explore 👇
our Membership offer 💕

{membership_link}

and it's also our secure
payment page 🌈

Click here to Join 👇
{membership_link}""",

            # B1 Shake-up 1 - Social Proof (T+20 min)
            'B1_SHAKEUP': """Hey {name} 💫

Inner Joy is thriving! 🌸
Anna, Josephine, Emma and Chloe
just became members 💕

Come join us and create
more Joy in your life 🌈

Here's our Membership Page 👇
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

            # B1 S3 - Sales Offer 3 (Next morning Sun/Mon 9:00 AM)
            'B1_S3': """Hi {name} 🌞
Good morning!

Still thinking about the
playful session with Ineke? 💫

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
            'B1_M1': """Congratulations, {name}! 🌸

You're now a member of
Renew Your Inner Joy ✨

This Zoom link gives you
full access Monday to Friday —
daily live 20-minute sessions
at 20:00 / 20:30 (UTC+8)

This week's Zoom link:
{member_zoom_link}

This week's YouTube link for
the recordings:
{youtube_playlist_link}

💛 So happy to have you with us 💖

Ineke""",

            # B1 M1a1 - Member Welcome (Fair Trial)
            'B1_M1A1': """Congratulations, {name}! 🌸

Your Fair Trial is active:
{trial_start} → {trial_end}

Friendly heads-up:
on day 7, ({trial_day7}) we'll remind you.
If you take no action,
your trial will roll into
the full 3-month membership.

This Zoom link gives you
full access Monday to Friday —
daily live 20-minute sessions
at 20:00 / 20:30 (UTC+8)

This week's Zoom link:
{member_zoom_link}

💛 So happy you've joined""",

            # B1 NoSales + NoShow - Combined Friday Follow-up (18:00)
            # This message is sent to BOTH NoSales (attended but didn't buy) AND NoShow (didn't attend)
            # IMPORTANT: Requires Tier 2 approval from Meta (outbound message)
            # NOTE: Hold 5-6 weeks before sending (waiting for Tier 2 verification)
            'B1_NOSALES': """Hello {name} 🌸
I'd love to invite you again 💕

Join me this weekend for another
playful Inner Joy Zoom session 🌈


Come as you are —
comfy clothes, curious heart,
and a smile 😄

Free Zoom preview session link:
{zoom_link}

Choose your option 👇



A = Sat 15:30

B = Sat 19:30–21:30 (walk-in)

C = Sun 15:30

D = Sun 19:30–21:30 (walk-in)



All times in UTC+8 ⏰

Reply A, B, C or D



Or start your 3-month membership 💖
Renew Your Inner Joy — only $80
{membership_link}

Can't wait to see you again 🌼""",

            # B1 NoShow - Same as NoSales (combined template)
            # NOTE: Hold 5-6 weeks before sending (waiting for Tier 2 verification)
            'B1_NOSHOW': """Hello {name} 🌸
I'd love to invite you again 💕

Join me this weekend for another
playful Inner Joy Zoom session 🌈


Come as you are —
comfy clothes, curious heart,
and a smile 😄

Free Zoom preview session link:
{zoom_link}

Choose your option 👇



A = Sat 15:30

B = Sat 19:30–21:30 (walk-in)

C = Sun 15:30

D = Sun 19:30–21:30 (walk-in)



All times in UTC+8 ⏰

Reply A, B, C or D



Or start your 3-month membership 💖
Renew Your Inner Joy — only $80
{membership_link}

Can't wait to see you again 🌼""",

            # B2 Ra - No Timeslot Preference Reminder (Immediate when entering Tree 2)
            'B2_RA': """Hey {name}🌸
Here's your free Zoom link 🌈
{zoom_link}

Which day + time fits you best?
Choose your letter below 👇

A = Sat 15:30

B = Sat 19:30–21:30 (walk-in)

C = Sun 15:30

D = Sun 19:30–21:30 (walk-in)



All times in UTC+8 ⏰

Reply A, B, C or D 💫

Or: I already attended""",

            # B2 Rb - No Timeslot Preference Reminder (2 hours after B2 Ra)
            'B2_RB': """Hey {name}🌸
Here's your free Zoom link
{zoom_link}

Which day + time fits you best?
Choose your letter below 👇

A = Sat 15:30

B = Sat 19:30–21:30 (walk-in)

C = Sun 15:30

D = Sun 19:30–21:30 (walk-in)

All times in UTC+8 ⏰

Reply A, B, C or D""",

            # B2 S1 - Sales Offer 1 (Sunday afternoon 16:00)
            'B2_S1': """Hey {name}! 🌸

Is Inner Joy your new goal? 💫

3 Months Membership — $80 💖

Click below to explore 👇
our Membership offer 💕

{membership_link}

It's also our secure
payment page 🌈

Click here to join 👇
{membership_link}""",

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
        Get display text for a timeslot (e.g., 'Saturday 15:30' or 'Saturday 19:30-21:30 (walk-in)')

        Args:
            timeslot: Timeslot letter (A, B, C, D)

        Returns:
            Display text for the timeslot
        """
        if timeslot not in Config.TIME_SLOTS:
            return ''

        slot_info = Config.TIME_SLOTS[timeslot]
        day = slot_info['day']
        time_obj = slot_info['time']
        time_str = time_obj.strftime('%H:%M')

        # Check if this is a walk-in slot
        if slot_info.get('is_walkin', False):
            end_time = slot_info.get('end_time')
            if end_time:
                end_time_str = end_time.strftime('%H:%M')
                return f"{day} {time_str}–{end_time_str} (walk-in)"

        return f"{day} {time_str}"

    @staticmethod
    def get_window_duration(contact_source: str) -> int:
        """
        Get the appropriate window duration based on contact source

        Args:
            contact_source: Contact source ('facebook_ads' or 'website')

        Returns:
            Window duration in hours (72 for facebook_ads, 24 for website)
        """
        if contact_source == Config.SOURCE_FACEBOOK_ADS:
            return 72  # 72-hour window for Facebook Ads
        elif contact_source == Config.SOURCE_WEBSITE:
            return 24  # 24-hour window for Website/FB Page
        else:
            # Default to 24-hour window for unknown sources (conservative)
            return 24

    @staticmethod
    def validate_config():
        """Validate that required configuration is present"""
        required = ['RESPOND_API_KEY', 'GOOGLE_SHEETS_ID']
        missing = [key for key in required if not getattr(Config, key)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True
