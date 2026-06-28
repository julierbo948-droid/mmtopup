import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import Config
from handlers import start, buy_command, button_callback, handle_message, admin_add_balance, check_balance, check_transactions

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not Config.BOT_TOKEN:
        logging.error("BOT_TOKEN is not set in .env file. Please set it.")
        return
    if not Config.ADMIN_ID:
        logging.warning("ADMIN_ID is not set in .env file. Admin commands will not work.")

    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("add_balance", admin_add_balance))
    application.add_handler(CommandHandler("balance", check_balance))
    application.add_handler(CommandHandler("transactions", check_transactions))

    # Callback Query Handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Message Handler (for user ID, zone ID, and card details input)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
