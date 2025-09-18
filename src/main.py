import os
import asyncio
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    config = {
        "api_id": int(os.getenv("API_ID")),
        "api_hash": os.getenv("API_HASH"),
        "target_user_id": int(os.getenv("TARGET_USER_ID")),
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "session_name": os.getenv("SESSION_NAME", "default_session"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemma-3n-e4b-it"),
        "gemini_prompt": os.getenv("GEMINI_PROMPT"),
    }
    if not all(config.values()):
        raise ValueError("Error: Not all environment variables are set in the .env file.")
    return config

def initialize_gemini(api_key, model_name, prompt):
    """Initialize the Gemini model and chat."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        initial_history = [
            {"role": "user", "parts": [prompt]},
            {"role": "model", "parts": ["Ok, I understand my role. I'm ready."]},
        ]
        chat = model.start_chat(history=initial_history)
        logging.info(f"Gemini model '{model_name}' initialized successfully.")
        return chat
    except Exception as e:
        logging.error(f"Error initializing Gemini: {e}")
        raise

async def main():
    """Main function to run the bot."""
    try:
        config = load_config()
    except ValueError as e:
        logging.error(e)
        return

    chat = initialize_gemini(config["gemini_api_key"], config["gemini_model"], config["gemini_prompt"])
    client = TelegramClient(config["session_name"], config["api_id"], config["api_hash"])

    @client.on(events.NewMessage(from_users=config["target_user_id"], incoming=True))
    async def handle_new_message(event):
        """Handle new messages from the target user."""
        message_text = event.message.text
        logging.info(f"Received message from target user: '{message_text}'")
        async with client.action(event.chat_id, 'typing'):
            try:
                logging.info("Sending request to Gemini...")
                response = await chat.send_message_async(message_text)
                full_response = response.text
                await event.respond(full_response)
                logging.info(f"Response from Gemini: '{full_response}'")
            except Exception as e:
                logging.error(f"Error while interacting with Gemini: {e}")
                await event.respond("Sorry, something went wrong while processing your message.")

    try:
        logging.info("Client is starting...")
        await client.start()
        me = await client.get_me()
        logging.info(f"Logged in as: {me.first_name} {me.last_name or ''} (ID: {me.id})")
        logging.info(f"Bot is active and waiting for messages from user with ID: {config['target_user_id']}")
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"An error occurred while running the client: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
