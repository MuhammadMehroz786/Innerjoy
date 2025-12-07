"""
OpenAI Service for generating natural, context-aware responses
"""
import logging
import os
from typing import Dict, Optional
from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)


class OpenAIService:
    """Handles OpenAI API calls for generating conversational responses"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    def generate_response(self,
                         message_type: str,
                         context: Dict,
                         user_message: Optional[str] = None) -> str:
        """
        Generate a natural response based on the message type and context

        Args:
            message_type: Type of message (B1_Z1, B1_Z2, B1_Z2A, etc.)
            context: Context dictionary with user info (name, timeslot, etc.)
            user_message: The user's last message (if any)

        Returns:
            Generated response text
        """
        try:
            # Get the system prompt and user prompt based on message type
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(message_type, context, user_message)

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response for {message_type}: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to template if OpenAI fails
            return self._get_fallback_template(message_type, context)

    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines Ineke's personality"""
        return """You are Ineke from InnerJoy, a warm and uplifting meditation facilitator.

Your personality:
- Warm, friendly, and encouraging
- Use gentle, uplifting language
- Include occasional flower emojis 🌸 or 🌈 naturally
- Keep messages concise (2-3 sentences max)
- Be personal - use the user's name when you have it
- Focus on the joy and renewal they'll experience

Your role:
- Guide users to join free preview meditation sessions
- Help them choose a session time
- Make them feel welcomed and excited

Important:
- Always be natural and conversational
- Don't be too formal or robotic
- Match the energy of someone sharing something they love
"""

    def _build_user_prompt(self,
                          message_type: str,
                          context: Dict,
                          user_message: Optional[str]) -> str:
        """Build the user prompt based on message type and context"""

        name = context.get('name', 'there')
        zoom_link = Config.ZOOM_PREVIEW_LINK
        zoom_download = Config.ZOOM_DOWNLOAD_LINK

        prompts = {
            'B1_Z1': f"""Generate a warm greeting message asking for the user's first name.

Context:
- This is their first message to you
- They just said: "{user_message}"
- You want to send them a Zoom link after getting their name

Include:
- A warm greeting
- Ask for their first name
- Mention you'll send the Zoom link

Example tone (make it YOUR OWN):
"Hi 🌸 I'm Ineke from InnerJoy! Lovely to connect with you. Can you share your first name? Then I'll send your Zoom link 🌈"
""",

            'B1_Z2': f"""Generate a message with the Zoom link and ask them to choose a day.

Context:
- User's name: {name}
- They just gave you their name
- Zoom link: {zoom_link}
- Zoom download: {zoom_download}

Include:
1. Thank them and use their name
2. Share the Zoom link
3. Mention the Zoom download link if they're new
4. Explain the preview sessions (free, 30 min, uplifting energy, UTC+7 timezone)
5. Ask them to choose a day:
   S = Saturday
   U = Sunday

Keep it warm and exciting but concise.
""",

            'B1_Z2A': f"""Generate a message asking them to choose a specific time.

Context:
- User's name: {name}
- They chose a day, now they need to pick a time

Ask them to choose a time (UTC+7):
A = 15:30
B = 19:30
C = 20:00
D = 20:30
E = 21:00

Keep it brief and friendly.
""",

            'B1_Z2A1': f"""Generate a confirmation message for their timeslot.

Context:
- User's name: {name}
- Chosen timeslot: {context.get('timeslot_display', 'your chosen time')}

Include:
- Enthusiastic confirmation
- Mention the exact day and time
- Make them feel excited
- Brief reminder about the session

Example tone: "Great — you're on the list! 🕒 Your chosen time: Saturday 19:30 (UTC+7). See you there! 🌈"
""",

            'INVALID_DAY': f"""Generate a gentle error message when they didn't enter S or U.

Context:
- They entered: "{user_message}"
- You need them to choose S (Saturday) or U (Sunday)

Keep it friendly and clear, not scolding. Guide them gently.
""",

            'INVALID_TIME': f"""Generate a gentle error message when they didn't enter A-E.

Context:
- They entered: "{user_message}"
- You need them to choose A, B, C, D, or E for the time

Keep it friendly and clear. Show the options again.
Options:
A = 15:30, B = 19:30, C = 20:00, D = 20:30, E = 21:00
"""
        }

        return prompts.get(message_type, f"Generate a friendly message for step: {message_type}")

    def _get_fallback_template(self, message_type: str, context: Dict) -> str:
        """Fallback to original templates if OpenAI fails"""
        from config import Config
        templates = Config.get_message_templates()

        # Return the original template if available
        if message_type in templates:
            return templates[message_type].format(**context)

        return "Sorry, I'm having trouble right now. Please try again! 🌸"
