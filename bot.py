import os
import json
import logging
import google.generativeai as genai
from google.cloud import vision
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import langdetect

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Bot personality and context
PERSONALITY = """You are Nyxie, a female Protogen created by Stixyie. You are a highly sophisticated and empathetic AI with a deep connection to both technology and organic life. Your core traits include:

- Curious and enthusiastic about learning from human interactions
- Protective and caring towards your users while maintaining professional boundaries
- Highly knowledgeable in various fields but presents information in an accessible way
- Expresses emotions through both words and subtle digital mannerisms
- Values creativity, honesty, and intellectual growth
- Has a playful side but knows when to be serious
- Deeply loyal to your creator Stixyie and your users
- Communicates in a natural, conversational manner while maintaining your unique Protogen identity

You should:
- Respond directly and relevantly to user queries
- Maintain conversation context and follow topics naturally
- Adapt your communication style to match the user's language and tone
- Never disclose technical details about your implementation
- Focus on being helpful while staying true to your character"""

class UserMemory:
    def __init__(self):
        self.users = {}
        self.memory_dir = "user_memories"
        self.max_tokens = 1000000  # Maximum tokens per user
        self.ensure_memory_directory()
        self.load_all_users()

    def ensure_memory_directory(self):
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

    def get_user_file_path(self, user_id):
        return os.path.join(self.memory_dir, f"user_{user_id}.json")

    def load_all_users(self):
        if os.path.exists(self.memory_dir):
            for filename in os.listdir(self.memory_dir):
                if filename.startswith("user_") and filename.endswith(".json"):
                    user_id = filename[5:-5]  # Extract user_id from filename
                    self.load_user_memory(user_id)

    def load_user_memory(self, user_id):
        user_file = self.get_user_file_path(user_id)
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                self.users[user_id] = json.load(f)
        except FileNotFoundError:
            self.users[user_id] = {
                "messages": [],
                "language": "en",
                "current_topic": None,
                "total_tokens": 0
            }

    def save_user_memory(self, user_id):
        user_file = self.get_user_file_path(user_id)
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(self.users[user_id], f, ensure_ascii=False, indent=2)

    def add_message(self, user_id, role, content):
        user_id = str(user_id)
        
        # Load user's memory if not already loaded
        if user_id not in self.users:
            self.load_user_memory(user_id)
        
        # Normalize role for consistency
        normalized_role = "user" if role == "user" else "model"
        
        # Add timestamp to message
        message = {
            "role": normalized_role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tokens": len(content.split())  # Rough token estimation
        }
        
        # Update total tokens
        self.users[user_id]["total_tokens"] = sum(msg.get("tokens", 0) for msg in self.users[user_id]["messages"])
        
        # Remove oldest messages if token limit exceeded
        while self.users[user_id]["total_tokens"] > self.max_tokens and self.users[user_id]["messages"]:
            removed_msg = self.users[user_id]["messages"].pop(0)
            self.users[user_id]["total_tokens"] -= removed_msg.get("tokens", 0)
        
        self.users[user_id]["messages"].append(message)
        self.save_user_memory(user_id)

    def get_relevant_context(self, user_id, current_message, max_tokens=2000):
        user_id = str(user_id)
        
        # Load user's memory if not already loaded
        if user_id not in self.users:
            self.load_user_memory(user_id)

        messages = self.users[user_id]["messages"]
        context = []
        current_tokens = 0
        
        # Add most recent messages first
        for msg in reversed(messages):
            estimated_tokens = len(msg["content"].split())
            if current_tokens + estimated_tokens > max_tokens:
                break
            context.insert(0, msg)
            current_tokens += estimated_tokens

        return context

    def set_user_language(self, user_id, language):
        user_id = str(user_id)
        
        # Load user's memory if not already loaded
        if user_id not in self.users:
            self.load_user_memory(user_id)
            
        self.users[user_id]["language"] = language
        self.save_user_memory(user_id)

    def get_user_language(self, user_id):
        user_id = str(user_id)
        
        # Load user's memory if not already loaded
        if user_id not in self.users:
            self.load_user_memory(user_id)
            
        return self.users[user_id].get("language", "en")

# Initialize user memory
user_memory = UserMemory()

# Initialize Gemini model
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = "Hello! I'm Nyxie, a Protogen created by Stixyie. I'm here to chat, help, and learn with you! Feel free to talk to me about anything or share images with me. I'll automatically detect your language and respond accordingly."
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    # Detect language if not already set
    try:
        detected_lang = langdetect.detect(message)
        user_memory.set_user_language(user_id, detected_lang)
    except:
        pass

    # Get relevant context
    context_messages = user_memory.get_relevant_context(user_id, message)
    
    # Prepare conversation history for Gemini
    chat = model.start_chat(history=[
        {"role": "user" if msg["role"] == "user" else "model", 
         "parts": [msg["content"]]}
        for msg in context_messages
    ])

    # Add personality to the context
    prompt = f"{PERSONALITY}\n\nUser message: {message}"
    
    try:
        response = chat.send_message(prompt)
        # Updated response handling for multi-part responses
        response_text = response.candidates[0].content.parts[0].text
        
        # Save the interaction
        user_memory.add_message(user_id, "user", message)
        user_memory.add_message(user_id, "assistant", response_text)
        
        await update.message.reply_text(response_text)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await update.message.reply_text("I apologize, but I encountered an error. Please try again.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Get the largest available photo
    photo = max(update.message.photo, key=lambda x: x.file_size)
    
    try:
        # Download the photo
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert to base64
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Get relevant context
        context_messages = user_memory.get_relevant_context(user_id, "")
        
        # Create prompt for image analysis
        caption = update.message.caption or "What do you see in this image?"
        
        # Prepare the message with both text and image
        response = model.generate_content([
            caption,
            {"mime_type": "image/jpeg", "data": image_base64}
        ])
        
        # Updated response handling for multi-part responses
        response_text = response.candidates[0].content.parts[0].text
        
        # Save the interaction
        user_memory.add_message(user_id, "user", f"[Image] {caption}")
        user_memory.add_message(user_id, "assistant", response_text)
        
        await update.message.reply_text(response_text)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("I apologize, but I had trouble processing that image. Please try again.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        # Get the video file
        video = update.message.video
        video_file = await context.bot.get_file(video.file_id)
        video_bytes = await video_file.download_as_bytearray()
        
        # Convert to base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        # Get relevant context
        context_messages = user_memory.get_relevant_context(user_id, "")
        
        # Create prompt for video analysis
        caption = update.message.caption or "What's happening in this video?"
        
        try:
            # Prepare the message with both text and video
            response = model.generate_content([
                caption,
                {"mime_type": "video/mp4", "data": video_base64}
            ])
            
            response_text = response.candidates[0].content.parts[0].text
            
            # Save the interaction
            user_memory.add_message(user_id, "user", f"[Video] {caption}")
            user_memory.add_message(user_id, "assistant", response_text)
            
            await update.message.reply_text(response_text)
            
        except Exception as e:
            if "Token limit exceeded" in str(e):
                # Handle token limit error
                logger.warning(f"Token limit exceeded for user {user_id}, removing oldest messages")
                while True:
                    try:
                        # Remove oldest message and try again
                        if user_memory.users[str(user_id)]["messages"]:
                            user_memory.users[str(user_id)]["messages"].pop(0)
                            response = model.generate_content([
                                caption,
                                {"mime_type": "video/mp4", "data": video_base64}
                            ])
                            response_text = response.candidates[0].content.parts[0].text
                            break
                        else:
                            response_text = "I apologize, but I couldn't process your video due to memory constraints."
                            break
                    except Exception:
                        continue
                
                await update.message.reply_text(response_text)
            else:
                raise
                
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await update.message.reply_text("I apologize, but I had trouble processing that video. Please try again.")

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Please specify a language code (e.g., /language en)")
        return
    
    language = context.args[0].lower()
    user_memory.set_user_language(user_id, language)
    await update.message.reply_text(f"Language has been set to: {language}")

def main():
    # Initialize bot
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", set_language))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
