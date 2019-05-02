import websocket
import requests
import os
import time
import re
import logging
import json
logging.basicConfig()
import bs4
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from slackclient import SlackClient
from datetime import datetime
import user_count_license
import expiration_date

#export variables from .env file
project_folder = os.path.expanduser('/home/slackbot')
load_dotenv(os.path.join(project_folder, '.env'))

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
COMMANDS  = 'bitbucket license', 'jira license', 'confluence license', 'license', 'expiration date'
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(COMMANDS)

    # Finds and executes the given command, filling in response
    response =  None
    # This is where you start to implement more commands!

    if command.startswith('bitbucket license'):
         response = "Count of Bitbucket licenses: {}".format(user_count_license.bitbucket_license())
    elif command.startswith('jira license'):
         response = "Count of Jira Software licenses: {}".format(user_count_license.jira_license())
    elif command.startswith('confluence license'):
         response = "Count of Confluence licenses: {}".format(user_count_license.confluence_license())
    elif command.startswith('license'):
         response = "Count of Confluence licenses: {}\n Count of Jira licenses: {}\n Count of Bitbucket licenses: {}" \
         .format(user_count_license.confluence_license(),user_count_license.jira_license(),user_count_license.bitbucket_license())
    elif command.startswith('expiration date'):
         response = "Atlassian Applications Licenses will expire in: {} days".format(expiration_date.bitbucket_expiration_date())

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
