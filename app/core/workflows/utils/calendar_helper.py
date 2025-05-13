import datetime
import os
import pickle
import uuid
import logging
import re

# Try to import Google libraries, but provide fallback if not available
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logging.warning("Google Calendar API dependencies not installed. Using mock implementation.")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def authenticate_google_calendar():
    # If Google libraries aren't available, return None
    if not GOOGLE_AVAILABLE:
        logging.warning("Google Calendar authentication skipped - using mock implementation")
        return None
        
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.pkl', 'wb') as token:
                pickle.dump(creds, token)
        except FileNotFoundError:
            logging.error("credentials.json file not found. Cannot authenticate with Google.")
            return None
    service = build('calendar', 'v3', credentials=creds)
    return service

# Try to authenticate, but don't fail if it doesn't work
try:
    calendar_service = authenticate_google_calendar()
except Exception as e:
    logging.error(f"Failed to authenticate with Google Calendar: {str(e)}")
    calendar_service = None

def normalize_time_format(time_str):
    """Normalize various human time formats to a standard 'Hour AM/PM' format."""
    # Convert to lowercase and remove extra spaces
    time_str = time_str.lower().strip()
    
    # Handle common time expressions
    time_expressions = {
        "morning": "9 AM",
        "noon": "12 PM",
        "afternoon": "2 PM",
        "evening": "6 PM",
        "night": "8 PM",
    }
    
    if time_str in time_expressions:
        return time_expressions[time_str]
    
    # Clean up the input - remove all non-alphanumeric characters except colon
    cleaned = re.sub(r'[^0-9:apm]', '', time_str)
    
    # Extract hours, minutes, and am/pm indicator
    hour_match = re.search(r'(\d+)(?::(\d+))?', cleaned)
    if not hour_match:
        # Default to noon if we can't parse it
        logging.warning(f"Could not parse time '{time_str}', defaulting to noon")
        return "12 PM"
    
    hour = int(hour_match.group(1))
    minute = int(hour_match.group(2)) if hour_match.group(2) else 0
    
    # Determine AM/PM
    if "p" in cleaned or hour >= 12:
        am_pm = "PM"
        # Convert 24-hour format to 12-hour if needed
        if hour > 12:
            hour -= 12
    else:
        am_pm = "AM"
        # Convert 12 AM to 12
        if hour == 12:
            hour = 12
    
    # Format the time string
    if minute == 0:
        return f"{hour} {am_pm}"
    else:
        return f"{hour}:{minute:02d} {am_pm}"

def normalize_date_format(date_str):
    """Normalize various date formats to YYYY-MM-DD."""
    # Remove any non-numeric/dash characters
    date_str = re.sub(r'[^0-9\-/.]', '', date_str)
    
    # Try different date formats
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', 
        '%m-%d-%Y', '%m/%d/%Y', '%Y.%m.%d', '%d.%m.%Y', '%m.%d.%Y'
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.datetime.strptime(date_str, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If we couldn't parse the date, log a warning and return the original
    logging.warning(f"Could not parse date '{date_str}', using as is")
    return date_str

def create_calendar_event(name, date, time):
    """Create a calendar event with smart handling of date and time formats."""
    # If calendar service is not available, create a mock appointment link
    if calendar_service is None:
        appointment_id = str(uuid.uuid4())[:8]
        logging.info(f"Created mock appointment with ID {appointment_id} for {name} on {date} at {time}")
        return f"https://example.com/appointment/{appointment_id}"
    
    try:
        # Handle case when date is empty or invalid
        if not date or date.strip() == '':
            # Use tomorrow as default date
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            logging.warning(f"Empty date provided, defaulting to today: {date}")
        
        # Normalize date and time formats
        normalized_date = normalize_date_format(date)
        normalized_time = normalize_time_format(time)
        
        logging.info(f"Normalized date: {date} → {normalized_date}")
        logging.info(f"Normalized time: {time} → {normalized_time}")
        
        # Try different time formats
        dt_str = f"{normalized_date} {normalized_time}"
        
        try:
            # Try with minutes format (e.g., "3:30 PM")
            if ":" in normalized_time:
                event_start = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
            else:
                # Try without minutes (e.g., "3 PM")
                event_start = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I %p")
        except ValueError as e:
            # If both formats fail, use a fallback datetime
            logging.error(f"Error parsing datetime '{dt_str}': {str(e)}")
            fallback_time = datetime.datetime.now().replace(
                hour=14, minute=0, second=0, microsecond=0
            ) + datetime.timedelta(days=1)  # Tomorrow at 2 PM
            event_start = fallback_time
            logging.warning(f"Using fallback time: {event_start}")
            
        # Set appointment duration to 30 minutes
        event_end = event_start + datetime.timedelta(minutes=30)

        event = {
            'summary': f'Dental Appointment - {name}',
            'location': 'Dental Clinic',
            'description': f'Appointment for {name}',
            'start': {'dateTime': event_start.isoformat(), 'timeZone': 'Asia/Karachi'},
            'end': {'dateTime': event_end.isoformat(), 'timeZone': 'Asia/Karachi'},
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }

        if calendar_service is not None:
            event_result = calendar_service.events().insert(calendarId='primary', body=event).execute()
            return event_result.get('htmlLink')
        else:
            # Fallback to mock link
            appointment_id = str(uuid.uuid4())[:8]
            return f"https://example.com/appointment/{appointment_id}"
            
    except Exception as e:
        logging.error(f"Error creating calendar event: {str(e)}")
        # Fallback to mock appointment if Google Calendar fails
        appointment_id = str(uuid.uuid4())[:8]
        return f"https://example.com/appointment/{appointment_id}"
