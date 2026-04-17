import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update, context):

async def handle_file(update, context):
    doc = update.message.document
    file = await doc.get_file()
    await file.download_to_drive(doc.file_name)
    await update.message.reply_text(f"File mili: {doc.file_name}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.run_polling()
