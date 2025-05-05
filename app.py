import os
import json
import logging
import asyncio

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_channel_history import SlackChannelHistory

from ai_agent import create_agent
from parser import answer_parser

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

app = AsyncApp(
    token=SLACK_BOT_TOKEN,
    # This must be set to handle bot message events
    ignoring_self_assistant_message_events_enabled=False,
)

channel_social = SlackChannelHistory("social")

# Load users list from file
with open("users.json", "r") as f:
    users_store = json.load(f)

@app.event("app_mention")
async def handle_app_mention(event, say):
    """Handle app mention events in Slack.
    
    Args:
        event: The Slack event data
        say: Function to send a message back to Slack
    """
    try:
        async with create_agent() as agent:
            thread_ts = event.get("thread_ts") or event["ts"]
            
            # Get thread history
            response = channel_social.get_thread_history(thread_ts)
            conversation = ""
            for message in response:
                # Replace any user id in message["text"] with user name
                message_text = message["text"]
                for user_id, user_name in users_store.items():
                    message_text = message_text.replace(user_id, user_name)
                
                conversation += users_store[message["user"]] + ": " + message_text + "\n"

            # Send a typing message to the channel
            typing_message = await say(text="Bot is typing...", thread_ts=thread_ts)

            response = await agent.ainvoke({"messages": conversation})
            response_content = response["messages"][-1].content
            text = answer_parser.parse(response_content).answer

            await app.client.chat_update(
                channel=event["channel"],
                ts=typing_message["ts"],  # Timestamp of the "typing" message
                text=text,
                thread_ts=thread_ts
            )
            
    except Exception as e:
        logger.error(f"Error handling app mention: {str(e)}")
        await say(text="Sorry, I encountered an error while processing your request.", thread_ts=thread_ts)

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN, loop=loop)
        loop.run_until_complete(handler.start_async())
    except Exception as e:
        logger.error(f"Error starting Slack app: {str(e)}")
        raise