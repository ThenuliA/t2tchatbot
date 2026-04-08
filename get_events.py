from datetime import datetime
from typing import List, Dict, Optional
import requests


def get_all_events(silent: bool = False) -> List[Dict]:
    """
    Fetch all events from the API without filtering.
    Returns list of event dictionaries.
    """
    events_url = "https://t2t.lk/data/events.json"
    
    try:
        response = requests.get(events_url, timeout=10)
        response.raise_for_status()
        events_data = response.json()
        
        if not silent:
            print(f"Found {len(events_data)} total events")
        
        return events_data
        
    except Exception as e:
        if not silent:
            print(f"Error fetching events: {e}")
        return []


def parse_event_date(event: Dict) -> Optional[datetime]:
    """
    Parse event date from various possible fields and formats.
    Returns datetime object or None if parsing fails.
    """
    event_date_str = event.get('date') or event.get('eventDate') or event.get('start_date') or ''
    
    if not event_date_str:
        return None
    
    date_formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%B %d, %Y',
        '%d %B %Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(event_date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def filter_events_by_date_range(
    events: List[Dict],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    silent: bool = False
) -> List[Dict]:
    """
    Filter events by date range.
    If start_date is None, includes all events before end_date.
    If end_date is None, includes all events after start_date.
    """
    filtered = []
    
    for event in events:
        event_date = parse_event_date(event)
        
        # If no date found, include the event (assume it's valid)
        if event_date is None:
            filtered.append(event)
            if not silent:
                print(f"  Including event (no date found): {event.get('title', event.get('name', 'Unknown'))}")
            continue
        
        # Check date range
        if start_date and event_date < start_date:
            continue
        if end_date and event_date > end_date:
            continue
        
        filtered.append(event)
        if not silent:
            date_str = event.get('date') or event.get('eventDate') or event.get('start_date')
            print(f"  Including event: {event.get('title', event.get('name', 'Unknown'))} on {date_str}")
    
    if not silent:
        print(f"Filtered to {len(filtered)} events")
    
    return filtered


def get_future_events():
    """Fetch events from the API and filter for future dates only."""
    today = datetime.now()
    all_events = get_all_events(silent=False)
    return filter_events_by_date_range(all_events, start_date=today, silent=False)


def format_events_for_prompt(events):
    """Format events list into readable text for the system prompt."""
    if not events:
        return "No upcoming events available."
    
    formatted = []  
    for event in events:
        title = event.get('title') or event.get('name') or 'Untitled Event'
        date = event.get('date') or event.get('eventDate') or event.get('start_date') or 'Date TBD'
        description = event.get('description') or event.get('details') or ''
        location = event.get('location') or event.get('venue') or ''
        
        event_text = f"- {title}"
        if date:
            event_text += f" (Date: {date})"
        if location:
            event_text += f" at {location}"
        if description:
            event_text += f"\n  {description}"
        formatted.append(event_text)
    
    return "\n".join(formatted)