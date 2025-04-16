import os
import dotenv
import json
from datetime import datetime
from typing import List, Dict

from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from slack_channel_history import SlackChannelHistory


class SlackVectorDB:
    def __init__(self, channel_name: str = "social"):
        """Initialize the SlackVectorDB class.
        
        Args:
            channel_name: The name of the Slack channel to monitor
            chunk_size: Size of text chunks for splitting conversations
            chunk_overlap: Overlap between chunks to maintain context
        """
        dotenv.load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.channel_name = channel_name
        
        # Load users list
        with open("users.json", "r") as f:
            self.users_store = json.load(f)
            
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = Chroma(
            collection_name=f"slack_{channel_name}_history",
            embedding_function=self.embeddings,
            persist_directory="./chroma_slack_db",
        )
        
        # Initialize Slack channel history
        self.slack_channel_history = SlackChannelHistory(channel_name=channel_name)
        self.text_splitter = SemanticChunker(self.embeddings, breakpoint_threshold_type="gradient")

        # Track last processed timestamp
        self.last_processed_ts = self._load_last_processed_ts()
    
    def _load_last_processed_ts(self) -> float:
        """Load the last processed timestamp from a file."""
        try:
            with open(f"last_processed_{self.channel_name}.json", "r") as f:
                return float(json.load(f).get("last_ts", 0))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0.0
    
    def _save_last_processed_ts(self, timestamp: float):
        """Save the last processed timestamp to a file."""
        with open(f"last_processed_{self.channel_name}.json", "w") as f:
            json.dump({"last_ts": timestamp}, f)
    
    @staticmethod
    def timestamp_to_date(timestamp: str) -> str:
        """Convert Slack timestamp to readable date format.
        
        Args:
            timestamp: Slack message timestamp
            
        Returns:
            Formatted date string
        """
        return datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    
    def process_message(self, message: dict) -> str:
        """Process a single message and replace user IDs with names.
        
        Args:
            message: Slack message dictionary
            
        Returns:
            Processed message text
        """
        message_text = message["text"]
        for user_id, user_name in self.users_store.items():
            message_text = message_text.replace(user_id, user_name)
        return message_text
    
    def create_documents(self, thread_history: str, metadata: Dict) -> List[Document]:
        """Create documents from thread history using semantic chunking.
        
        Args:
            thread_history: The text content to split into documents
            metadata: Metadata to associate with the documents
            
        Returns:
            List of Document objects
        """
        # Skip processing if thread_history is empty or too short
        if not thread_history:
            return []
            
        try:
            documents = self.text_splitter.create_documents([thread_history], [metadata])
            return documents
        except Exception as e:
            print(f"Error creating documents: {e}")
            # If semantic chunking fails, fall back to simple document creation
            return [Document(page_content=thread_history, metadata=metadata)]
    
    def process_channel_history(self, batch_size: int = 100):
        """Process the channel history and add to vector store in batches."""
        channel_history = self.slack_channel_history.get_channel_history()
        documents_to_add = []
        latest_ts = self.last_processed_ts
        
        for message in channel_history:
            message_ts = float(message["ts"])
            if message_ts <= self.last_processed_ts:
                continue
                
            latest_ts = max(latest_ts, message_ts)
            thread_history = ""
            
            # Process main message
            permalink = self.slack_channel_history.get_permalink(message["ts"])
            processed_text = self.process_message(message)
            thread_history += f"{self.timestamp_to_date(message['ts'])} {self.users_store[message['user']]}: {processed_text}\n"
            
            # Process thread messages
            thread_ts = message.get("thread_ts")
            if thread_ts:
                thread_messages = self.slack_channel_history.get_thread_history(thread_ts)
                for thread_message in thread_messages:
                    processed_text = self.process_message(thread_message)
                    thread_history += f"{self.timestamp_to_date(thread_message['ts'])} {self.users_store[thread_message['user']]}: {processed_text}\n"
            
            # Create metadata
            metadata = {
                "permalink_to_message": permalink,
                "channel": self.channel_name,
                "message_ts": message["ts"],
                "thread_ts": thread_ts,
                "user": self.users_store[message["user"]],
                "message_type": "thread" if thread_ts else "main"
            }
            
            # Create and add documents to batch
            documents = self.create_documents(thread_history, metadata)
            documents_to_add.extend(documents)

            # Process in batches
            if len(documents_to_add) >= batch_size:
                try:
                    self.vector_store.add_documents(documents_to_add)
                    documents_to_add = []
                except Exception as e:
                    print(f"Error adding documents: {e}")
                    # Retry logic could be added here
        
        # Process remaining documents
        if documents_to_add:
            try:
                self.vector_store.add_documents(documents_to_add)
            except Exception as e:
                print(f"Error adding final documents: {e}")
        
        # Update last processed timestamp
        if latest_ts > self.last_processed_ts:
            self._save_last_processed_ts(latest_ts)
            self.last_processed_ts = latest_ts

# Example usage
if __name__ == "__main__":
    vector_db = SlackVectorDB(channel_name="social")
    vector_db.process_channel_history()
