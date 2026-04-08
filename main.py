"""
main.py
T2T Chatbot — uses a daily-refreshed knowledge cache.
On startup it checks whether t2t_knowledge.txt was written today.
  - Same date  → reads from file (fast startup)
  - Different date or missing → re-scrapes the website and events, writes fresh cache

This module provides:
- ChatbotEngine class: Reusable chatbot logic (used by both CLI and API)
- main() function: Command-line interface
"""

from google.genai import types
from google import genai
from dotenv import load_dotenv
import os
from typing import Tuple, Optional

from get_events import get_future_events, format_events_for_prompt
from scrape_data import get_deep_website_data
from data_cache import is_cache_fresh, read_cache, write_cache


WEBSITE_URL = "https://t2t.lk/"


def refresh_and_cache() -> Tuple[str, str]:
    """Scrape all data and write it to the cache file. Returns (website_content, events_text)."""
    print("Fetching deep website data... please wait.")
    website_content = get_deep_website_data(WEBSITE_URL)

    print("\nFetching upcoming events...")
    future_events = get_future_events()
    events_text = format_events_for_prompt(future_events)

    write_cache(website_content, events_text)
    return website_content, events_text


def load_knowledge() -> Tuple[str, str]:
    """
    Load knowledge from cache if it's fresh, otherwise re-scrape and cache.
    Returns (website_content, events_text).
    """
    if is_cache_fresh():
        print("Cache is up-to-date. Loading knowledge from file...")
        website_content, events_text = read_cache()
        if website_content is not None:
            return website_content, events_text
        print("Cache read failed — re-scraping instead.")

    print("Cache is outdated or missing. Re-scraping data...")
    return refresh_and_cache()


def build_system_prompt(website_content: str, events_text: str) -> str:
    """Build system prompt for Gemini AI with T2T knowledge."""
    return f"""
You are a helpful and professional AI assistant for Theory to Trade (T2T).

DO NOT make up program descriptions or program names. Use ONLY the information provided below and the information taken from the website.

Your role:
- Ask about the user's background (student, graduate, career stage, field of study)
- Based on their background, recommend suitable programs
- Inform users about UPCOMING events (only future events are listed below)

WEBSITE DATA:
{website_content}

UPCOMING EVENTS (These are confirmed future events only):
{events_text}

SALES APPROACH:
- For IT/Computer Science students/graduates: Recommend CRISP Foundation or CRISP Practitioner
- For filmmakers/creative professionals: Recommend IFAP
- Proactively mention relevant upcoming events based on user's interests
- If a user asks about events, only mention the events listed above (they are all confirmed future events)

REGISTRATION LINKS:
- If a user wants to register as a STUDENT, provide this link: https://t2t.lk/t2t-platform/index.html
- If a user wants to register as a MENTOR, provide this link: https://t2t.lk/t2t-platform/add-mentor.html
- Offer these links proactively when the user shows interest in joining programs or contributing as a mentor
"""


class ChatbotEngine:
    """
    Core chatbot engine using Google Gemini AI.
    Can be used by both CLI (main.py) and API (api.py).
    """
    
    def __init__(self):
        """Initialize empty engine."""
        self.client: Optional[genai.Client] = None
        self.system_prompt: str = ""
        self.chat_sessions: dict = {}
        self.model_name: str = 'gemini-2.5-flash'
        self.website_content: str = ""
        self.events_text: str = ""
    
    def initialize(self):
        """
        Load knowledge, setup Gemini client, and build system prompt.
        Call this once before using chat().
        """
        load_dotenv()
        
        # Initialize Gemini client
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        
        # Load or refresh knowledge
        self.website_content, self.events_text = load_knowledge()
        self.system_prompt = build_system_prompt(self.website_content, self.events_text)
        
        print("ChatbotEngine initialized successfully.")
    
    def chat(self, message: str, session_id: str = "default") -> str:
        """
        Process a chat message and return the bot's response.
        
        Args:
            message: User's input message
            session_id: Session identifier for maintaining conversation history
        
        Returns:
            Bot's response text
        """
        if not self.client:
            raise RuntimeError("ChatbotEngine not initialized. Call initialize() first.")
        
        # Get or create chat history for this session
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        
        chat_history = self.chat_sessions[session_id]
        
        # Add user message to history
        chat_history.append(types.Content(role='user', parts=[types.Part(text=message)]))
        
        # Generate response using Gemini
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=chat_history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=0.3
            )
        )
        
        bot_response = response.text
        
        # Add bot response to history
        chat_history.append(types.Content(role='model', parts=[types.Part(text=bot_response)]))
        
        # Keep history manageable (last 20 messages)
        if len(chat_history) > 20:
            self.chat_sessions[session_id] = chat_history[-20:]
        
        return bot_response
    
    def get_cached_knowledge(self) -> Tuple[str, str]:
        """
        Get the cached knowledge data.
        
        Returns:
            Tuple of (website_content, events_text)
        """
        return self.website_content, self.events_text


def main():
    """Command-line interface for T2T chatbot."""
    # Create and initialize engine
    engine = ChatbotEngine()
    engine.initialize()
    
    print("\nChatbot: Hello! I have updated my knowledge on T2T programs and upcoming events. Let me know a bit about yourself")
    
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        
        # Use engine to get response
        bot_response = engine.chat(user_input, session_id="cli")
        print(f"Chatbot: {bot_response}\n")


if __name__ == "__main__":
    main()