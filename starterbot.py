import os
import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from slackclient import SlackClient

from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from config import DAILY_NOTIFY_CHANNEL
from config import BOT_ID
from config import SLACK_BOT_TOKEN

import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


engine = create_engine( SQLALCHEMY_DATABASE_URI, echo=False)

Base = declarative_base()

class Event(Base):
    """
    A table to store data on craigslist listings.
    """

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    date = Column(String)
    location = Column(String)
    start_time = Column(String)
    end_time = Column(String)

Base.metadata.create_all(engine)

session = scoped_session(sessionmaker(bind=engine))



# constants
AT_BOT = "<@" + BOT_ID + ">"
CREATE_EVENT_COMMAND = "create event"
GET_EVENT_COMMAND = "get event"
GET_EVENTS_ON_COMMAND = "get events on"
GET_LAST_COMMAND = "get last"
GET_TODAY_COMMAND = "get events today"
DELETE_EVENT_COMMAND = "delete event"
HELP_COMMAND = "help"


# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)


def niceify_response(event_id, description, location, start_time, end_time, date):
    """
    Return nice looking response on slack
    """
    return ( "*******************" + "\n" + "Id: " + str(event_id) + "\n"+ "Description: " + description + "\n" 
    + "Location: " + location + "\n" + "Start Time: " + start_time + "\n" + "End Time: "
    + end_time + "\n" + "Date: " + date + "\n" + "*******************" + "\n" ) 

def find_largest_id():
    """
    Use clunky and un-pythonic code to find largest id
    TODO:Make this function nicer
    """
    max_id_val= 0
    for event in session.query(Event).all():
        if event.id > max_id_val:
            max_id_val = event.id
    return max_id_val

def handle_time(time_string):
    """
    Parses input and makes it look nice for the output
    """
    if "am" in time_string.lower():
        numerical_time = time_string.lower().split("am")[0]
        return numerical_time + " " + "AM"
    elif "pm" in time_string.lower():
        numerical_time = time_string.lower().split("pm")[0]
        return numerical_time + " " + "PM"
    return None

def handle_date(date_string):
    """
    Parse date input and make it look nicer for the output
    """
    date_arr = date_string.split("/")
    year = "20" + date_arr[2].strip()
    month = date_arr[0].strip()
    if month[0] == "0":
        month = month[1]
    day = date_arr[1].strip()
    if day[0] == "0":
        day = day[1]
    return year + "-" + month + "-" + day
    


def handle_create_event(command):
    """
    Parse input for create event and restructure it for filling the columns 
    related to the event model
    """

    event_string = command.split(CREATE_EVENT_COMMAND,1)[1].strip()
    if "desc:" in event_string and "loc:" in event_string and "date:" in event_string and "time:" in event_string:
        description = ((event_string.split("desc:"))[1].split(",")[0]).strip()
        location = ((event_string.split("loc:"))[1].split(",")[0]).strip()
        times = ((event_string.split("time:"))[1].split(",")[0]).strip().split("-")
        start_time = handle_time(times[0].strip())
        end_time = handle_time(times[1].strip())
        date = handle_date(((event_string.split("date:"))[1].split(",")[0]).strip())

        if len(session.query(Event).all()) > 0:
            id_val = find_largest_id() + 1
        else:
            id_val = 1

        return Event(id = id_val, description = description, start_time = start_time, end_time = end_time, 
            date = date, location = location)
    else:
        raise ValueError('Bad Event. You are missing an input. Remember to specify *desc:* , *loc:*, *date:*, and *time:*')
        return None

def handle_command(command, channel, daily_response=False):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """

    #Default response with the help command
    response = "Not sure what you mean. Use the *" + HELP_COMMAND + \
               "* command with numbers, delimited by spaces."


    #Create an event
    if command.startswith(CREATE_EVENT_COMMAND):
        try:
            event = handle_create_event(command)
            session.add(event)
            session.commit()
            response = ("You have successfully created the following event: \n" + 
            niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date))

        except Exception as e:
            response = str(e)

    #Get events on a date
    elif command.startswith(GET_EVENTS_ON_COMMAND):
        try:
            event_date= command.split(GET_EVENTS_ON_COMMAND)[1].strip()
            events = session.query(Event).filter(Event.date == handle_date(event_date))
            response = ""
            if events.count() == 0:
                response = "There are no events on " + event_date

            for event in events:
                response += niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date)

        except Exception as e:
            response = str(e)

    #Get last created events for purpose of modificaiton/deletion or whatever
    elif command.startswith(GET_LAST_COMMAND):
        try:
            event_number= command.split(GET_LAST_COMMAND)[1].strip()
            events = session.query(Event).order_by(Event.id.desc()).limit(event_number)

            #events = reversed(conn.execute(query).fetchall())
            response = ""
            if events.count() == 0:
                response = "You have no events"
            for event in events:
                response += niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date)
        except Exception as e:
            response = str(e)

    #Get events for today
    elif command.startswith(GET_TODAY_COMMAND):
        try:
            event_date = time.strftime("%x")
            events = session.query(Event).filter(Event.date == handle_date(event_date))
            response = ""
            if events.count() == 0:
                response = "There are no events today"

            for event in events:
                response += niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date)
        except Exception as e:
            response = str(e)

    #Get event based on id
    elif command.startswith(GET_EVENT_COMMAND):
        try:
            event_id = command.split(GET_EVENT_COMMAND)[1].strip()
            event = session.query(Event).filter(Event.id == int(event_id)).first()
            response = niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date)
        except Exception as e:
            response = str(e)

    #Delete event based on id
    elif command.startswith(DELETE_EVENT_COMMAND):
        try:
            event_id = command.split(DELETE_EVENT_COMMAND)[1].strip()
            event = session.query(Event).filter(Event.id == int(event_id)).first()
            session.delete(event)
            session.commit()
            response = "You have deleted the following event \n" + niceify_response(event.id, event.description, event.location, event.start_time, event.end_time, event.date)
        except Exception as e:
            response = str(e)

    #Help command listing different functions
    elif command.startswith(HELP_COMMAND):
        try:
            response = ("Use on of the following commands:\n" + \
                "*create event* to create an event with *desc:*, *loc:*, *time:*, and *date:* \n" + \
                "Example: *create event* desc: This is my event description, loc: Fondren, time: 3pm-6pm, date: 2/28/17 \n" + \
                "*get events on* with a date formatted as month/day/year (2/28/17) to get all events on that date \n" + \
                 "Example: *get events on* 2/29/17\n" + \
                "*get last* with a number to indicate how many of the last created events to get\n" + \
                "Example: *get last* 5\n" + \
                "*get events today* to retrieve all events for today\n" + \
                "*get event* with a number to indicate the id of the event to get\n" + \
                "Example: *get event* 3\n" + \
                "*delete event* with a number to indicate the id of the event to delete\n" + \
                "Example: *delete event* 5\n")
        except Exception as e:
            response = str(e)

    #Add some nice headers for daily response
    if (daily_response):
        response = "Here are your events for today: \n" + response


    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None

def daily_report():
    #Wrap daily report in a different method
    handle_command("get events today", DAILY_NOTIFY_CHANNEL, True)


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    # func=daily_report,
    # trigger=IntervalTrigger(seconds=5),
    # id='get_day_events_job',
    # name='Print todays events every five seconds',
    # replace_existing=True)

    func=daily_report,
    trigger='cron', hour='6', minute='45')

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)

            time.sleep(READ_WEBSOCKET_DELAY)




    else:
        print(SLACK_BOT_TOKEN)
        print(BOT_ID)
        print(DAILY_NOTIFY_CHANNEL)
        print("Connection failed. Invalid Slack token or bot ID?")

