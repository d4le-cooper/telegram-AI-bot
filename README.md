# Telegram Bot

This project is a Telegram bot built using Python and the Telebot library. The bot responds to user commands, analyzes user messages, and provides personalized interactions based on user behavior.

## Features

- **Command Handling**: Responds to commands like `/start`, `/help`, `/reset`, `/utenti`, and `/carattere`.
- **User Personality Analysis**: Analyzes user messages to determine their personality traits.
- **Message Logging**: Logs all messages for analysis and debugging.
- **Custom AI Responses**: Generates AI-based responses tailored to user input and personality.
- **Group Chat Support**: Responds to mentions and keywords in group chats.
- **Automatic Data Saving**: Periodically saves user data and conversation history.

## Project Structure

```
telegram-bot/
├── src/
│   ├── bot.py          # Main logic for the Telegram bot
│   ├── config.py       # Configuration settings
│   ├── ai_service.py   # AI-based services for personality analysis and responses
│   ├── data_manager.py # Handles user data and conversation history
│   └── logger.py       # Logs messages and extracts data from logs
├── data/               # Stores user data and conversation history
├── logs/               # Stores message logs
├── .env                # Environment variables
├── .gitignore          # Files to ignore by Git
├── requirements.txt    # Project dependencies
├── Procfile            # Deployment configuration
└── README.md           # Project documentation
```

## Setup Instructions

1. **Clone the repository:**

   ```
   git clone <repository-url>
   cd telegram-bot
   ```

2. **Create a virtual environment:**

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory and add your bot token and API keys:
   ```
   BOT_TOKEN='your_bot_token_here'
   HF_API_KEY='your_huggingface_api_key_here'
   OPENAI_API_KEY='your_openai_api_key_here'
   DEEPSEEK_API_KEY='your_deepseek_api_key_here'
   ```

## Usage

To run the bot locally, execute the following command:

```
python src/bot.py
```

## Commands

- `/start` or `/help`: Displays a welcome message and usage instructions.
- `/reset`: Resets the conversation history for the current chat.
- `/utenti`: Lists all users who have interacted with the bot in the current chat, along with their personality traits (if analyzed).
- `/carattere`: Displays the personality traits of the user or a replied-to user.
- `/logs`: (Admin only) Displays the most recent logs.

## Deployment

For deployment on platforms like Heroku, ensure you have a `Procfile` set up with the following content:

```
worker: python src/bot.py
```

## Contributing

Feel free to submit issues or pull requests for any improvements or features you'd like to see!

## License

This project is licensed under the MIT License. See the LICENSE file for details.
