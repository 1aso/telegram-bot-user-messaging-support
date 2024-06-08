import logging
import asyncio
from telegram.error import BadRequest, NetworkError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from pyrogram import Client
from pyrogram.errors import RPCError, UserNotParticipant, UsernameInvalid, PeerFlood
import os
from dotenv import load_dotenv
from aiolimiter import AsyncLimiter
import re

# Load environment variables from .env file
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Mediator account information
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
SUPPORT_CHAT_ID = os.getenv('SUPPORT_CHAT_ID')

# Verify that SUPPORT_CHAT_ID is set
if not SUPPORT_CHAT_ID:
    raise ValueError("SUPPORT_CHAT_ID must be set in the .env file")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store temporary user data
user_data = {}

# Create a custom path for the session file
SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)
SESSION_PATH = os.path.join(SESSION_DIR, "my_account")

# Limiter to allow 1 message per 5 seconds
limiter = AsyncLimiter(1, 5)

def check_user_subscription(user_id: int, context: CallbackContext) -> bool:
    """Check if the user is subscribed to the channel"""
    try:
        member = context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest as e:
        logger.error(f"Failed to check subscription for user {user_id}: {e}")
        return False

def button(update: Update, context: CallbackContext) -> None:
    """Handle button presses"""
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'check_subscription':
        if check_user_subscription(user_id, context):
            query.answer()
            new_text = "YOUR MESSAGE"
            if query.message.text != new_text:
                query.edit_message_text(text=new_text)
            user_data[user_id] = {'stage': 'USERNAME', 'started': True}
        else:
            query.answer("YOUR MESSAGE")
            keyboard = [
                [InlineKeyboardButton("YOUR MESSAGE", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            new_text = f'YOUR MESSAGE @{CHANNEL_USERNAME}'
            if query.message.text != new_text:
                query.edit_message_text(
                    text=new_text,
                    reply_markup=reply_markup
                )
    elif query.data == 'contact_support':
        query.answer()
        query.edit_message_text(text="YOUR MESSAGE")
        user_data[user_id] = {'stage': 'SUPPORT_MESSAGE', 'started': True}

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message and ask for the target username"""
    user_id = update.message.from_user.id
    user_data[user_id] = {'started': True}  # Mark the user as having used /start
    if check_user_subscription(user_id, context):
        update.message.reply_text(
            'YOUR MESSAGE'
        )
        user_data[user_id]['stage'] = 'USERNAME'
    else:
        keyboard = [
            [InlineKeyboardButton("YOUR MESSAGE", callback_data='check_subscription')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f'YOUR MESSAGE @{CHANNEL_USERNAME}',
            reply_markup=reply_markup
        )

def get_username(update: Update, context: CallbackContext) -> None:
    """Store the target username and ask for the message"""
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get('stage') == 'USERNAME':
        username = update.message.text.strip()
        if not username.startswith("@"):
            username = "@" + username  # Add "@" if not included
        user_data[user_id]['username'] = username
        user_data[user_id]['stage'] = 'MESSAGE'
        update.message.reply_text(
            f'YOUR MESSAGE{username}:'
        )
    elif user_data.get(user_id, {}).get('stage') == 'MESSAGE':
        get_message(update, context)
    elif user_data.get(user_id, {}).get('stage') == 'SUPPORT_MESSAGE':
        contact_support(update, context)

def get_message(update: Update, context: CallbackContext) -> None:
    """Store the message and send it to the mediator account"""
    message = update.message.text
    user_id = update.message.from_user.id

    if user_id in user_data and user_data[user_id].get('stage') == 'MESSAGE':
        username = user_data[user_id]['username']
        logger.info(f"Sending message to username: {username}")
        if asyncio.run(send_to_mediator(username, message)):
            # Add "@" when sending message back to the user
            update.message.reply_text(f'YOUR MESSAGE{username}')
        else:
            keyboard = [
                [InlineKeyboardButton("YOUR MESSAGE", callback_data='contact_support')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'YOUR MESSAGE',
                reply_markup=reply_markup
            )
        user_data.pop(user_id)
    else:
        update.message.reply_text('YOUR MESSAGE')

def contact_support(update: Update, context: CallbackContext) -> None:
    """Handle support message"""
    message = update.message.text
    user_id = update.message.from_user.id

    if user_id in user_data and user_data[user_id].get('stage') == 'SUPPORT_MESSAGE':
        user_info = update.message.from_user
        support_message = f"YOUR MESSAGE@{user_info.username} (ID: {user_info.id}):\n\n{message}"
        if send_support_message(context, support_message):
            update.message.reply_text('YOUR MESSAGE')
        else:
            update.message.reply_text('YOUR MESSAGE')
        user_data.pop(user_id)
    else:
        update.message.reply_text('YOUR MESSAGE')

def send_support_message(context: CallbackContext, message: str) -> bool:
    """Send the support message to the support chat via the bot"""
    try:
        context.bot.send_message(chat_id=SUPPORT_CHAT_ID, text=message)
        logger.info(f"Support message sent to {SUPPORT_CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"Failed to send support message: {e}")
        return False

async def send_to_mediator(username: str, message: str) -> bool:
    """Send the message to the mediator account"""
    app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    async with app:
        try:
            async with limiter:
                user = await app.get_users(username)
                logger.info(f"User details: {user}")
                await app.send_message(user.id, message)
                logger.info(f"Message sent to {username}")
                return True
        except UsernameInvalid:
            logger.error(f"Username {username} is invalid.")
            return False
        except PeerFlood:
            logger.error(f"Account is currently limited. Cannot send message to {username}.")
            return False
        except RPCError as e:
            logger.error(f"Failed to send message to {username}: {e}")
            return False

def check_start(update: Update, context: CallbackContext) -> None:
    """Check if the user used the /start command before any other message"""
    user_id = update.message.from_user.id
    if not user_data.get(user_id, {}).get('started'):
        update.message.reply_text('YOUR MESSAGE')
    else:
        # Continue processing the message based on the current stage
        stage = user_data[user_id].get('stage')
        if stage == 'USERNAME':
            get_username(update, context)
        elif stage == 'MESSAGE':
            get_message(update, context)
        elif stage == 'SUPPORT_MESSAGE':
            contact_support(update, context)

def filter_non_text_messages(update: Update, context: CallbackContext) -> None:
    """Filter out non-text messages and inform the user"""
    update.message.reply_text('YOUR MESSAGE')

def filter_messages_with_urls(update: Update, context: CallbackContext) -> None:
    """Filter out messages containing URLs and inform the user"""
    if re.search(r'(?i)http[s]?://', update.message.text):  # (?i) makes the pattern case-insensitive
        update.message.reply_text('YOUR MESSAGE')
    else:
        # Continue processing the text message based on the current stage
        check_start(update, context)

def main() -> None:
    """Start the bot"""
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Command and message handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, filter_messages_with_urls))
    dispatcher.add_handler(MessageHandler(Filters.photo | Filters.document | Filters.audio | Filters.voice, filter_non_text_messages))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
