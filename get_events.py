from datetime import datetime
import requests

def get_future_events():
    """Fetch events from the API and filter for future dates only."""
    events_url = "https://t2t.lk/data/events.json"
    future_events = []
    today = datetime.now()
    
    try:
        response = requests.get(events_url, timeout=10)
        response.raise_for_status()
        events_data = response.json()
        
        print(f"Found {len(events_data)} total events")
        
        for event in events_data:
            event_date_str = event.get('date') or event.get('eventDate') or event.get('start_date') or ''
            
            if event_date_str:
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
                # has multiple date formats so that an event isnt missed out
                
                event_date = None
                for fmt in date_formats:
                    try:
                        event_date = datetime.strptime(event_date_str.strip(), fmt) # sets date to correct format (to date format)
                        break
                    except ValueError:
                        continue
                
                if event_date and event_date >= today:
                    future_events.append(event)
                    print(f"  Including future event: {event.get('title', event.get('name', 'Unknown'))} on {event_date_str}")
                elif event_date:
                    print(f"  Skipping past event: {event.get('title', event.get('name', 'Unknown'))} on {event_date_str}")
            else:
                future_events.append(event)
                print(f"  Including event (no date found): {event.get('title', event.get('name', 'Unknown'))}")
        
        print(f"Filtered to {len(future_events)} future events")
        return future_events
        
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []


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