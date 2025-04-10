import os
import asyncio
import logging
from typing import Any, Dict

# The default is the aiohttp based implementation
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt import App
from slack_channel_history import SlackChannelHistory
from ai_agent import MCPAgentRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in environment variables")

app = App(
    token=SLACK_BOT_TOKEN,
    # This must be set to handle bot message events
    ignoring_self_assistant_message_events_enabled=False,
)

ai_agent = MCPAgentRunner()
channel_social = SlackChannelHistory("social")

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle app mention events in Slack.
    
    Args:
        event: The Slack event data
        say: Function to send a message back to Slack
    """
    try:
        thread_ts = event.get("thread_ts") or event["ts"]
        
        # Get thread history
        response = channel_social.get_thread_history(thread_ts)
        history = ""
        latest_message = response[-1]["text"]
        for message in response[:-1]:
            history += message["user"] + ": " + message["text"] + "\n"
        
        prompt = f"""
        Lịch sử chat trong thread: {history}
        Tin nhắn gần nhất: {latest_message}
        """

        # Run the agent in a new event loop
        typing_message = say(text="Bot is typing...", thread_ts=thread_ts)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(ai_agent.run(prompt))
            # say(text=response, thread_ts=thread_ts)
            app.client.chat_update(
                            channel=event["channel"],
                            ts=typing_message["ts"],  # Timestamp of the "typing" message
                            text=response,
                            thread_ts=thread_ts
                        )
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error handling app mention: {str(e)}")
        say(text="Sorry, I encountered an error while processing your request.", thread_ts=thread_ts)

if __name__ == "__main__":
    try:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    except Exception as e:
        logger.error(f"Error starting Slack app: {str(e)}")
        raise