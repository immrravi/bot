import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from scraper import InstagramScraper
from utils import is_valid_reel_url
from excel import export_to_excel
from database import init_db, get_user_balance, add_credits, deduct_credits, set_credits
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Global semaphore to limit concurrent scraping tasks to 8
SCRAPING_SEMAPHORE = asyncio.Semaphore(8)

# Get Telegram Bot Token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Define Admin ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Cost per reel found in the output
REEL_COST_PER_ITEM = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message and user_id when the command /start is issued."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"👋 Welcome to the Instagram Reel Scraper Bot!\n\n"
        f"Your User ID: `{user_id}`\n\n"
        "Send me an Instagram Reel URL, and I will collect all reels uploaded by that user after that specific reel.\n\n"
        f"💰 **Cost**: {REEL_COST_PER_ITEM} credit per reel found in the output.\n\n"
        "Use /balance to check your credits.\n"
        "Use /buy to see payment instructions.\n\n"
       
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user's current credit balance."""
    user_id = update.effective_user.id
    credits = await asyncio.to_thread(get_user_balance, user_id)
    await update.message.reply_text(f"💳 Your current credit balance is: {credits} credits.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment instructions and credit plans."""
    payment_instructions = (
        "💰 To buy credits:\n\n"
        "📌 UPI ID:\n"
        "`rudraksha75@ptaxis`\n\n"
        "👤 Name: Yagyesh Singh\n\n"
        "Credit Plans:\n"
        "- ₹50 → 250 credits\n"
        "- ₹100 → 500 credits\n"
        "- ₹200 → 1200 credits\n"
        "- ₹500 → 3500 credits\n"
        "- ₹1000 → 8000 credits\n\n"
        "📸 Send payment screenshot after paying."
    )
    await update.message.reply_text(payment_instructions, parse_mode=ParseMode.MARKDOWN)

# =========================
# ADMIN COMMANDS
# =========================

async def addcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to add credits to a user."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /addcredit user_id amount")
            return
        target_user_id = int(args[0])
        amount = int(args[1])
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be a positive number.")
            return
        await asyncio.to_thread(add_credits, target_user_id, amount)
        current_balance = await asyncio.to_thread(get_user_balance, target_user_id)
        await update.message.reply_text(
            f"✅ Successfully added {amount} credits to user `{target_user_id}`.\n"
            f"New balance for user `{target_user_id}`: {current_balance} credits."
        )
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ {amount} credits have been added to your account. Your new balance is {current_balance} credits."
            )
        except Exception as e:
            logging.error(f"Could not notify user {target_user_id}: {e}")
    except ValueError:
        await update.message.reply_text("Usage: /addcredit user_id amount")
    except Exception as e:
        logging.error(f"Error in addcredit command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

async def deductcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to deduct credits from a user safely."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /deductcredit user_id amount")
            return
        target_user_id = int(args[0])
        amount = int(args[1])
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be a positive number.")
            return
            
        success = await asyncio.to_thread(deduct_credits, target_user_id, amount)
        if success:
            await update.message.reply_text(f"✅ Deducted {amount} credits from user {target_user_id}")
            try:
                new_balance = await asyncio.to_thread(get_user_balance, target_user_id)
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"💳 {amount} credits have been deducted from your account. Your new balance is {new_balance} credits."
                )
            except Exception as e:
                logging.error(f"Could not notify user {target_user_id}: {e}")
        else:
            await update.message.reply_text("❌ Not enough credits")
            
    except ValueError:
        await update.message.reply_text("Usage: /deductcredit user_id amount")
    except Exception as e:
        logging.error(f"Error in deductcredit command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

async def setcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to overwrite credits for a user."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /setcredit user_id amount")
            return
        target_user_id = int(args[0])
        amount = int(args[1])
        if amount < 0:
            await update.message.reply_text("❌ Amount cannot be negative.")
            return
            
        await asyncio.to_thread(set_credits, target_user_id, amount)
        await update.message.reply_text(f"✅ Set credits to {amount} for user {target_user_id}")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💳 Your credit balance has been set to {amount} credits by the admin."
            )
        except Exception as e:
            logging.error(f"Could not notify user {target_user_id}: {e}")
            
    except ValueError:
        await update.message.reply_text("Usage: /setcredit user_id amount")
    except Exception as e:
        logging.error(f"Error in setcredit command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

async def sendmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to send a custom message to a specific user."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /sendmsg <user_id> <your message>")
            return
        target_user_id = int(args[0])
        message_text = " ".join(args[1:])
        
        if not message_text:
            await update.message.reply_text("❌ Message cannot be empty.")
            return

        try:
            await context.bot.send_message(chat_id=target_user_id, text=message_text)
            await update.message.reply_text(f"✅ Message sent to user {target_user_id}.")
        except Exception as e:
            logging.error(f"Could not send message to user {target_user_id}: {e}")
            await update.message.reply_text(f"❌ Failed to send message to user {target_user_id}. Error: {e}")
            
    except ValueError:
        await update.message.reply_text("Usage: /sendmsg <user_id> <your message>")
    except Exception as e:
        logging.error(f"Error in sendmsg command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {str(e)}")

# =========================
# MESSAGE HANDLERS
# =========================

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming payment proofs and forward to admin."""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No Username"
    admin_message = f"🔔 **New Payment Proof Received!**\n\n" \
                    f"👤 User: {user.full_name} (@{username})\n" \
                    f"🆔 User ID: `{user_id}`\n"
    if update.message.text:
        admin_message += f"📝 Message/UTR: {update.message.text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    elif update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=admin_message)
    elif update.message.document:
        doc_file_id = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=doc_file_id, caption=admin_message)
    await update.message.reply_text(
        "✅ Thank you! Your payment proof has been sent to the admin for verification. "
        "Credits will be added to your account shortly."
    )

async def run_scraping_task(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """The actual scraping task that runs concurrently."""
    user_id = update.effective_user.id
    
    # Check for cookies.json
    if not os.path.exists('cookies.json'):
        await update.message.reply_text("⚠️ Error: 'cookies.json' not found on the server.")
        return

    status_message = await update.message.reply_text("🔍 Valid URL received! Waiting for a slot in the concurrent queue...")
    
    async with SCRAPING_SEMAPHORE:
        await status_message.edit_text("🚀 Slot acquired! Starting the scraping process... This may take a few minutes.")
        
        scraper = InstagramScraper(cookies_path='cookies.json')
        output_file = f"reels_{user_id}_{int(asyncio.get_event_loop().time())}.xlsx"
        
        try:
            await scraper.init_browser(headless=True)
            await status_message.edit_text("⏳ Extracting reel info (username and date)...")
            username, target_date = await scraper.get_reel_info(text)
            
            await status_message.edit_text(f"👤 User: @{username}\n📅 Target Date: {target_date.strftime('%Y-%m-%d')}\n\n🔄 Collecting reels...")
            reels_data = await scraper.scrape_profile_reels(username, text)
            
            if not reels_data:
                await status_message.edit_text("ℹ️ No new reels found after the target date.")
                return

            total_reels = len(reels_data)
            total_cost = total_reels * REEL_COST_PER_ITEM
            
            current_credits = await asyncio.to_thread(get_user_balance, user_id)
            if current_credits < total_cost:
                await status_message.edit_text(
                    f"❌ Found {total_reels} reels, which costs {total_cost} credits. "
                    f"However, you only have {current_credits} credits."
                )
                return

            # Deduct credits using the new database function
            success_deduct = await asyncio.to_thread(deduct_credits, user_id, total_cost)
            if not success_deduct:
                await status_message.edit_text("❌ Failed to deduct credits. Please check your balance.")
                return
                
            new_balance = await asyncio.to_thread(get_user_balance, user_id)
            
            await status_message.edit_text(f"📊 Found {total_reels} reels. Deducted {total_cost} credits. Your new balance: {new_balance} credits.\nGenerating Excel file...")
            success_export = await asyncio.to_thread(export_to_excel, reels_data, output_file)
            
            if success_export:
                await status_message.edit_text(f"✅ Done! Collected {total_reels} reels. Sending the file...")
                with open(output_file, 'rb') as f:
                    await update.message.reply_document(document=f, filename="reels_output.xlsx")
                await update.message.reply_text(
                    f"✅ Task completed!\n\n📊 Reels collected: {total_reels}\n💸 Credits used: {total_cost}\n💳 Remaining balance: {new_balance} credits"
                )
            else:
                # Refund credits if export fails
                await asyncio.to_thread(add_credits, user_id, total_cost)
                await status_message.edit_text("❌ Failed to export data to Excel. Your credits have been refunded.")
                
        except Exception as e:
            logging.error(f"Error during scraping for user {user_id}: {e}")
            await update.message.reply_text(f"❌ An error occurred: {str(e)}")
        finally:
            await scraper.close()
            if os.path.exists(output_file):
                try: os.remove(output_file)
                except: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and start scraping tasks concurrently."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not is_valid_reel_url(text):
        await handle_payment_proof(update, context)
        return

    current_credits = await asyncio.to_thread(get_user_balance, user_id)
    if current_credits < 1:
        await update.message.reply_text("❌ Insufficient credits! Use /buy to purchase more.")
        return

    # START THE TASK CONCURRENTLY WITHOUT AWAITING IT
    asyncio.create_task(run_scraping_task(update, context, text))

def main():
    """Start the bot."""
    # Initialize the database
    try:
        init_db()
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("buy", buy))
    
    # Admin Command Handlers
    application.add_handler(CommandHandler("addcredit", addcredit))
    application.add_handler(CommandHandler("deductcredit", deductcredit))
    application.add_handler(CommandHandler("setcredit", setcredit))
    application.add_handler(CommandHandler("sendmsg", sendmsg))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE | filters.Document.PDF, handle_payment_proof))
    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()