# SLACK BOT

A Python-based platform for Slack integration with AI capabilities, providing intelligent message processing and response generation.

## Project Structure

```
mcp/
├── src/
│    ├── core/           # Core application components
│    │   ├── app.py
│    │   └── mcp_server.py
│    ├── slack/          # Slack integration components
│    │   ├── get_user_list.py
│    │   └── slack_channel_history.py
│    ├── ai/            # AI-related components
│    │   ├── ai_agent.py
│    │   └── create_vector_db.py
│    └── utils/         # Utility functions and helpers
│        ├── parser.py
│        └── tools.py
├── tests/                 # Test files
├── docs/                  # Documentation
├── requirements.txt       # Project dependencies
└── .env.example          # Example environment variables
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your Slack API credentials and other configuration.

## Development

- The project uses a modular structure to separate concerns:
  - `core/`: Contains the main application logic and server components
  - `slack/`: Handles Slack API integration and message processing
  - `ai/`: Contains AI-related functionality and vector database operations
  - `utils/`: Common utility functions and helpers

## Running the Application

```bash
python -m src.core.app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]
