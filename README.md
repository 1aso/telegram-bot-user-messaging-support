# Telegram Bot User Messaging Support

## Description
This is a Telegram bot designed to facilitate user messaging and support. The bot allows users to send messages to specific usernames and contact support for assistance. It ensures that users are subscribed to a specific channel before sending messages and provides a streamlined process for user support.

## Features
- **Subscription Verification**: Check if users are subscribed to a specific channel before allowing interactions.
- **User Messaging**: Allow users to send messages to specific usernames.
- **Support Contact**: Enable users to contact support directly through the bot.
- **Rate Limiting**: Implement rate limiting to prevent spam.
- **Session Management**: Store user session information for smoother interactions.

## Installation

### Prerequisites
- Python 3.8 or higher
- A Telegram bot token (you can get one from [BotFather](https://core.telegram.org/bots#6-botfather))
- API ID and Hash from [my.telegram.org](https://my.telegram.org)

### Steps
1. Clone the repository:
    ```bash
    git clone https://github.com/1aso/telegram-bot-messaging-support.git
    ```
2. Navigate to the project directory:
    ```bash
    cd telegram-bot-messaging-support
    ```
3. Create and activate a virtual environment (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Setup
1. Create a `.env` file in the root directory and add your bot credentials:
    ```dotenv
    BOT_TOKEN=your-telegram-bot-token
    API_ID=your-api-id
    API_HASH=your-api-hash
    SESSION_STRING=your-session-string
    CHANNEL_USERNAME=your-channel-username
    SUPPORT_CHAT_ID=your-support-chat-id
    ```
2. Ensure that the `sessions` directory exists:
    ```bash
    mkdir -p sessions
    ```

## Usage
1. Run the bot:
    ```bash
    python bot.py
    ```

## Project Structure
- `bot.py`: The main script containing the bot logic.
- `requirements.txt`: A list of Python dependencies.
- `.env`: Environment variables for sensitive information.
- `sessions/`: Directory to store session files.

## Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License
This project is licensed under the [MIT License](LICENSE).

## Acknowledgements
Special thanks to the [Telegram](https://core.telegram.org/bots) and [Pyrogram](https://docs.pyrogram.org/) communities for their extensive documentation and support.
 
