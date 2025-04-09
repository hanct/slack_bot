import os
import dotenv
import logging
from typing import List, Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


dotenv.load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")


class SlackChannelHistory:
    def __init__(self, channel_name: str):
        """Initialize the SlackChannelHistory class.
        
        Args:
            channel_name: The name of the Slack channel to monitor
        """
        self.client = WebClient(token=SLACK_BOT_TOKEN)
        self.channel_id = self.get_channel_id(channel_name)


    def get_thread_history(self, thread_ts: str) -> List[Dict]:
        try:
            response = self.client.conversations_replies(channel=self.channel_id, ts=thread_ts)
            return response['messages']
        except SlackApiError as e:
            logging.error(f"Error fetching thread history: {e}")
            return []
        
    # Slack channel history
    def get_channel_history(self) -> List[Dict]:
        try:
            response = self.client.conversations_history(channel=self.channel_id)
            return response['messages']
        except SlackApiError as e:
            logging.error(f"Error fetching channel history: {e}")
            return []

    # Get channel ID
    def get_channel_id(self, channel_name: str) -> str:
        """Get the channel ID for a given channel name.
        
        Args:
            channel_name: The name of the Slack channel
            
        Returns:
            The channel ID if found, empty string otherwise
        """
        try:
            response = self.client.conversations_list()
            # Search through all channels to find matching name
            for channel in response['channels']:
                if channel['name'] == channel_name:
                    return channel['id']
            logging.warning(f"Channel '{channel_name}' not found")
            return ""
        except SlackApiError as e:
            logging.error(f"Error fetching channel ID: {e}")
            return ""


