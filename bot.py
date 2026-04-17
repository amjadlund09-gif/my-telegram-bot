cat > bot.py << 'EOF'
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("8633631861:AAGPNODuoccYDTZFpDcTaC5HOnyLuuo1FQg")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! APK file bhejo, main analyze karunga!")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    file_name = doc.file_name
    await file.download_to_drive(file_name)
    await update.message.reply_text(f"File mili: {file_name}\nAnalysis shuru...")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

print("Bot chal raha hai...")
app.run_polling()
EOF
