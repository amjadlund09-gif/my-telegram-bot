
TOKEN = os.environ.get("8633631861:AAGPNODuoccYDTZFpDcTaC5HOnyLuuo1FQg")async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! File bhejo mujhe!")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    await file.download_to_drive(f"received_{doc.file_name}")
    await update.message.reply_text(f"File mil gayi: {doc.file_name}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

print("Bot chal raha hai...")
app.run_polling()
