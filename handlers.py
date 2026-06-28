from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from database import Database
from package import get_package_info
from helpers import auto_topup_playwright
import asyncio

db = Database()

# User states
WAITING_FOR_USER_ID = 1
WAITING_FOR_ZONE_ID = 2
CONFIRMATION = 3
WAITING_FOR_PAYMENT_METHOD = 4
WAITING_FOR_CARD_DETAILS = 5
PROCESSING_AUTO_TOPUP = 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    user = await db.get_user(user_id)
    if not user:
        user = await db.create_user(user_id, username)

    welcome_message = (
        f"မင်္ဂလာပါ {username}! 🙏\n\n"
        "Codashop မှ Mobile Legends Diamonds ဝယ်ယူနိုင်သော Bot မှ ကြိုဆိုပါတယ်။\n\n"
        f"လက်ကျန်ငွေ: {user["balance"]} Ks\n\n"
        "ဝယ်ယူရန် /buy ကိုနှိပ်ပါ။"
    )
    await update.message.reply_text(welcome_message)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data[chat_id] = {}
    
    keyboard = []
    row = []
    for key, value in Config.DIAMOND_PACKAGES.items():
        button_text = f"{value["diamonds"]} - {value["price"]} Ks"
        row.append(InlineKeyboardButton(button_text, callback_data=f"pkg_{key}"))
        if len(row) == 2: # Two buttons per row
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ဝယ်ယူလိုသော Diamond ပမာဏကို ရွေးချယ်ပါ:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data
    
    if data.startswith("pkg_"):
        pkg_key = data.split("_")[1]
        context.user_data[chat_id]["package"] = pkg_key
        
        await query.edit_message_text(
            text=f"သင်ရွေးချယ်ထားသော ပမာဏ: {Config.DIAMOND_PACKAGES[pkg_key]["diamonds"]}\n\n"
                 f"ကျေးဇူးပြု၍ သင်၏ Mobile Legends User ID ကို ရိုက်ထည့်ပါ။\n"
                 f"(ဥပမာ: 12345678)"
        )
        context.user_data[chat_id]["state"] = WAITING_FOR_USER_ID
    
    elif data == "confirm_order":
        pkg_key = context.user_data[chat_id]["package"]
        price = Config.DIAMOND_PACKAGES[pkg_key]["price"]
        
        keyboard = [
            [InlineKeyboardButton("💳 Bot Wallet ဖြင့် အလိုအလျောက် ဝယ်မည်", callback_data="auto_topup_wallet")],
            [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"ကျသင့်ငွေ: {price} Ks\n\n"
                 "ငွေပေးချေမှု နည်းလမ်းကို ရွေးချယ်ပါ။",
            reply_markup=reply_markup
        )
        context.user_data[chat_id]["state"] = WAITING_FOR_PAYMENT_METHOD

    elif data == "cancel_order":
        await query.edit_message_text(text="အော်ဒါကို ပယ်ဖျက်လိုက်ပါပြီ။ ဝယ်ယူရန် /buy ကို ပြန်နှိပ်ပါ။")
        if chat_id in context.user_data:
            del context.user_data[chat_id]

    elif data == "auto_topup_wallet":
        user_db = await db.get_user(chat_id)
        if not user_db:
            await query.edit_message_text("အသုံးပြုသူအချက်အလက် မတွေ့ပါ။ /start ကို ပြန်နှိပ်ပါ။")
            return

        pkg_key = context.user_data[chat_id]["package"]
        package_info = get_package_info(pkg_key)
        price = package_info["price"]

        if user_db["balance"] >= price:
            user_id_ml = context.user_data[chat_id]["user_id"]
            zone_id_ml = context.user_data[chat_id]["zone_id"]
            playwright_index = package_info["playwright_index"]
            card_details = {
                "number": Config.VISA_CARD_NUMBER,
                "expiry": Config.VISA_CARD_EXPIRY,
                "cvv": Config.VISA_CARD_CVV
            }

            await query.edit_message_text("Bot Wallet မှ ငွေဖြတ်ပြီး အလိုအလျောက် Diamond ဖြည့်သွင်းနေပါသည်... ခဏစောင့်ပါ။")
            context.user_data[chat_id]["state"] = PROCESSING_AUTO_TOPUP

            try:
                # Execute auto top-up using Playwright
                status = await auto_topup_playwright(user_id_ml, zone_id_ml, playwright_index, card_details)
                if "success" in status.lower(): # Assuming 'success' in status indicates successful transaction
                    new_balance = await db.update_balance(chat_id, -price)
                    await db.log_transaction(chat_id, "diamond_purchase", -price, f"MLBB Diamond {package_info["diamonds"]} for {user_id_ml}({zone_id_ml})")
                    await query.message.reply_text(
                        f"✅ Diamond ဖြည့်သွင်းမှု အောင်မြင်ပါသည်။\n"
                        f"သင့်လက်ကျန်ငွေ: {new_balance} Ks\n"
                        "အားပေးမှုကို ကျေးဇူးတင်ပါတယ်။"
                    )
                else:
                    await query.message.reply_text(f"အလိုအလျောက် Diamond ဖြည့်သွင်းမှု မအောင်မြင်ပါ။: {status}")
                    await db.log_transaction(chat_id, "diamond_purchase", -price, f"MLBB Diamond {package_info["diamonds"]} for {user_id_ml}({zone_id_ml})", status="failed")
            except Exception as e:
                await query.message.reply_text(f"အလိုအလျောက် Diamond ဖြည့်သွင်းရာတွင် အမှားအယွင်း ဖြစ်ပွားခဲ့ပါသည်။: {e}")
                await db.log_transaction(chat_id, "diamond_purchase", -price, f"MLBB Diamond {package_info["diamonds"]} for {user_id_ml}({zone_id_ml})", status="error")
            finally:
                if chat_id in context.user_data:
                    del context.user_data[chat_id]
        else:
            await query.edit_message_text(
                f"သင့်လက်ကျန်ငွေ {user_db["balance"]} Ks သည် Diamond ဝယ်ယူရန် မလုံလောက်ပါ။ ({price} Ks လိုအပ်သည်)\n\n"
                "Bot Owner မှ ငွေဖြည့်ပေးရန် ဆက်သွယ်ပါ။"
            )
            if chat_id in context.user_data:
                del context.user_data[chat_id]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if chat_id not in context.user_data:
        await update.message.reply_text("အော်ဒါစတင်ရန် /buy ကို နှိပ်ပါ။")
        return

    current_state = context.user_data[chat_id].get("state")

    if current_state == WAITING_FOR_USER_ID:
        context.user_data[chat_id]["user_id"] = text
        context.user_data[chat_id]["state"] = WAITING_FOR_ZONE_ID
        await update.message.reply_text(
            f"User ID: {text} ရရှိပါပြီ။\n\n"
            f"ကျေးဇူးပြု၍ သင်၏ Zone ID ကို ရိုက်ထည့်ပါ။\n"
            f"(ဥပမာ: 1234)"
        )
    elif current_state == WAITING_FOR_ZONE_ID:
        context.user_data[chat_id]["zone_id"] = text
        context.user_data[chat_id]["state"] = CONFIRMATION
        
        pkg_key = context.user_data[chat_id]["package"]
        pkg_info = get_package_info(pkg_key)
        user_id_ml = context.user_data[chat_id]["user_id"]
        zone_id_ml = text
        
        summary = (
            "🧾 **အော်ဒါ အချက်အလက်များ**\n\n"
            f"🎮 User ID: {user_id_ml} ({zone_id_ml})\n"
            f"💎 Diamond: {pkg_info["diamonds"]}\n"
            f"💰 ကျသင့်ငွေ: {pkg_info["price"]} Ks\n\n"
            "အထက်ပါအချက်အလက်များ မှန်ကန်ပါသလား?"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ မှန်ကန်သည် (ငွေပေးချေမည်)", callback_data="confirm_order")],
            [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="cancel_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode="Markdown")

async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != Config.ADMIN_ID:
        await update.message.reply_text("သင်သည် Bot Admin မဟုတ်ပါ။")
        return

    try:
        _, target_user_id_str, amount_str = update.message.text.split()
        target_user_id = int(target_user_id_str)
        amount = int(amount_str)

        if amount <= 0:
            await update.message.reply_text("ထည့်သွင်းမည့်ပမာဏသည် သုညထက်ကြီးရပါမည်။")
            return

        user = await db.get_user(target_user_id)
        if not user:
            await update.message.reply_text(f"User ID {target_user_id} ကို မတွေ့ပါ။")
            return

        new_balance = await db.update_balance(target_user_id, amount)
        await db.log_transaction(target_user_id, "deposit", amount, f"Admin added {amount} Ks")
        await update.message.reply_text(f"User ID {target_user_id} ၏ လက်ကျန်ငွေကို {amount} Ks ထည့်ပြီးပါပြီ။ လက်ကျန်ငွေ: {new_balance} Ks")
        
        # Notify the user whose balance was updated
        await context.bot.send_message(chat_id=target_user_id, text=f"သင့် Bot Wallet ထဲသို့ {amount} Ks ဖြည့်ပေးလိုက်ပါပြီ။ လက်ကျန်ငွေ: {new_balance} Ks")

    except ValueError:
        await update.message.reply_text("အသုံးပြုပုံမှားယွင်းနေပါသည်။ /add_balance <user_id> <amount> ဥပမာ: /add_balance 123456789 10000")
    except Exception as e:
        await update.message.reply_text(f"အမှားအယွင်း ဖြစ်ပွားခဲ့ပါသည်။: {e}")

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    if user:
        await update.message.reply_text(f"သင့်လက်ကျန်ငွေ: {user["balance"]} Ks")
    else:
        await update.message.reply_text("အသုံးပြုသူအချက်အလက် မတွေ့ပါ။ /start ကို ပြန်နှိပ်ပါ။")

async def check_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transactions = await db.get_transactions(user_id)
    if transactions:
        message = "**နောက်ဆုံး Transaction များ:**\n\n"
        for t in transactions:
            message += f"- {t["timestamp"].strftime("%Y-%m-%d %H:%M")} | {t["description"]} | {t["amount"]} Ks | Status: {t["status"]}\n"
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text("Transaction မှတ်တမ်း မရှိသေးပါ။")
