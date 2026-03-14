"""
main.py
T2T Chatbot — uses a daily-refreshed knowledge cache.
On startup it checks whether t2t_knowledge.txt was written today.
  - Same date  → reads from file (fast startup)
  - Different date or missing → re-scrapes the website and events, writes fresh cache
"""

from google.genai import types
from google import genai
from dotenv import load_dotenv
import os

from get_events import get_future_events, format_events_for_prompt
from scrape_data import get_deep_website_data
from data_cache import is_cache_fresh, read_cache, write_cache


WEBSITE_URL = "https://t2t.lk/"


def refresh_and_cache():
    """Scrape all data and write it to the cache file. Returns (website_content, events_text)."""
    print("Fetching deep website data... please wait.")
    website_content = get_deep_website_data(WEBSITE_URL)

    print("\nFetching upcoming events...")
    future_events = get_future_events()
    events_text = format_events_for_prompt(future_events)

    write_cache(website_content, events_text)
    return website_content, events_text


def load_knowledge():
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


def main():
    load_dotenv()
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
    model_name = 'gemini-2.5-flash'

    # Load or refresh knowledge
    website_content, events_text = load_knowledge()
    system_prompt = build_system_prompt(website_content, events_text)

    chat_history = []
    print("\nChatbot: Hello! I have updated my knowledge on T2T programs and upcoming events. Let me know a bit about yourself")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            break

        chat_history.append(types.Content(role='user', parts=[types.Part(text=user_input)]))

        response = client.models.generate_content(
            model=model_name,
            contents=chat_history,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )

        bot_response = response.text
        chat_history.append(types.Content(role='model', parts=[types.Part(text=bot_response)]))
        print(f"Chatbot: {bot_response}\n")


if __name__ == "__main__":
    main()