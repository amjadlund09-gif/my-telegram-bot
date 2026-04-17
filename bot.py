import os
import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
from PIL import Image
from reportlab.pdfgen import canvas

# --- Configuration & Logging ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8633631861:AAGPNODuoccYDTZFpDcTaC5HOnyLuuo1FQg")
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
async def clean_up(file_path: str):
    """Deletes the file after a short delay."""
    await asyncio.sleep(60) # Keep for 1 min then delete
    if os.path.exists(file_path):
        os.remove(file_path)

# --- Core Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me any file (Image or Document) and I'll help you process it.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.effective_attachment.get_file()
    original_name = update.message.effective_attachment.file_name
    
    # Save file details to user_data for state management
    file_ext = os.path.splitext(original_name)[1].lower()
    local_path = TEMP_DIR / f"{update.effective_user.id}_{original_name}"
    
    await file.download_to_drive(custom_path=local_path)
    context.user_data['current_file'] = str(local_path)
    context.user_data['original_name'] = original_name

    keyboard = [
        [InlineKeyboardButton("Rename", callback_data="rename")],
        [InlineKeyboardButton("Compress", callback_data="compress")]
    ]
    
    # Specific options based on format
    if file_ext in ['.jpg', '.jpeg', '.png']:
        keyboard.append([InlineKeyboardButton("Convert to PNG/JPG", callback_data="convert_img")])
    elif file_ext == '.txt':
        keyboard.append([InlineKeyboardButton("Convert to PDF", callback_data="convert_pdf")])
        keyboard.append([InlineKeyboardButton("Read Text", callback_data="extract_text")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Received: {original_name}\nWhat do you want to do?", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    file_path = context.user_data.get('current_file')
    if not file_path or not os.path.exists(file_path):
        await query.edit_message_text("Error: File not found or session expired.")
        return

    status_msg = await query.edit_message_text("Processing... ⚙️")

    try:
        if choice == "rename":
            await query.edit_message_text("Please reply with the new name (including extension).")
            context.user_data['awaiting_rename'] = True
            return

        elif choice == "convert_pdf":
            output_path = file_path.replace(".txt", ".pdf")
            c = canvas.Canvas(output_path)
            with open(file_path, 'r') as f:
                text = f.read()
                c.drawString(100, 750, text[:500]) # Simplified conversion
            c.save()
            await send_and_clean(update, context, output_path)

        elif choice == "convert_img":
            img = Image.open(file_path)
            rgb_img = img.convert('RGB')
            output_path = file_path.rsplit('.', 1)[0] + "_converted.jpg"
            rgb_img.save(output_path, "JPEG")
            await send_and_clean(update, context, output_path)

        elif choice == "extract_text":
            with open(file_path, 'r') as f:
                content = f.read(1000) # Send first 1000 chars
            await query.message.reply_text(f"File Content Preview:\n\n{content}")

        elif choice == "compress":
            # Simple compression logic for images
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                img = Image.open(file_path)
                output_path = file_path.rsplit('.', 1)[0] + "_compressed.jpg"
                img.save(output_path, "JPEG", quality=20)
                await send_and_clean(update, context, output_path)
            else:
                await query.edit_message_text("Compression only supported for images currently.")

    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text("An error occurred during processing.")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles renaming after the user provides a new name."""
    if context.user_data.get('awaiting_rename'):
        new_name = update.message.text
        old_path = context.user_data.get('current_file')
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        
        os.rename(old_path, new_path)
        context.user_data['awaiting_rename'] = False
        await send_and_clean(update, context, new_path)

async def send_and_clean(update: Update, context: ContextTypes.DEFAULT_TYPE, output_path: str):
    """Sends the processed file back and triggers deletion."""
    with open(output_path, 'rb') as doc:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=doc)
    
    # Schedule cleanup
    asyncio.create_task(clean_up(output_path))
    if context.user_data.get('current_file'):
        asyncio.create_task(clean_up(context.user_data['current_file']))

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ATTACHMENT, handle_document))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_input))
    
    print("Bot is running...")
    application.run_polling()
