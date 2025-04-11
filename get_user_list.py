import json
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

users_store = {}

# Put users into the dict
def save_users(users_array):
    for user in users_array:
        # Key user info on their unique user ID
        user_id = user["id"]
        # Store the entire user object (you may not need all of the info)
        users_store[user_id] = user["real_name"]

    # Save the users to a file
    with open("users.json", "w") as f:
        json.dump(users_store, f)
        

try:
    # Call the users.list method using the WebClient
    # users.list requires the users:read scope
    result = client.users_list()
    save_users(result["members"])

except SlackApiError as e:
    logger.error("Error creating conversation: {}".format(e))

