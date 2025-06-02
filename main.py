import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import speedtest
import subprocess
import re
import platform
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Telegram Bot Token
TOKEN = os.getenv("TOKEN")

def escape_markdown_v2(text: str) -> str:
    """Helper function to escape special characters for MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when /start is issued."""
    user = update.effective_user
    try:
        escaped_name = escape_markdown_v2(user.full_name)
        message = (
            f"Hi \\[{escaped_name}\\]\\({user.id}\\)\\!\n\n"
            "🚀 *Welcome to SpeedTest Bot*\n"
            "   *By: Bang Ale*\n\n"
            "📋 *Available commands:*\n"
            "┣ `/start` \\- Start the bot\n"
            "┣ `/help` \\- Show help\n"
            "┣ `/speedtest` \\- Run basic speed test\n"
            "┣ `/speedtest_advanced` \\- Run detailed speed test\n"
            "┗ `/ping <host>` \\- Ping a host\n\n"
            "🔹 *Example:* `/ping google\\.com`"
        )
        await update.message.reply_markdown_v2(message)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when /help is issued."""
    try:
        message = (
            "🛠 *Help Center*\n\n"
            "📋 *Available commands:*\n"
            "┣ `/start` \\- Start the bot\n"
            "┣ `/help` \\- Show this help\n"
            "┣ `/speedtest` \\- Run basic speed test\n"
            "┣ `/speedtest_advanced` \\- Run detailed speed test\n"
            "┗ `/ping <host>` \\- Ping a host\n\n"
            "🔹 *Basic SpeedTest:*\n"
            "`/speedtest` \\- Tests download, upload speeds and ping\n\n"
            "🔹 *Advanced SpeedTest:*\n"
            "`/speedtest_advanced` \\- Includes server and ISP details\n\n"
            "🔹 *Ping Test:*\n"
            "`/ping google.com` \\- Pings the specified host"
        )
        await update.message.reply_markdown_v2(message)
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def speedtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run basic speed test."""
    try:
        msg = await update.message.reply_text("⏳ Running speed test... This may take a minute")
        
        st = speedtest.Speedtest()
        st.get_best_server()
        
        download = st.download() / 1_000_000  # Mbps
        upload = st.upload() / 1_000_000  # Mbps
        ping = st.results.ping
        
        result = (
            "📊 *SpeedTest Results*\n\n"
            f"⬇️ *Download:* `{download:.2f} Mbps`\n"
            f"⬆️ *Upload:* `{upload:.2f} Mbps`\n"
            f"🏓 *Ping:* `{ping:.2f} ms`"
        )
        
        await msg.edit_text(result, parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Error in speedtest command: {e}")
        await update.message.reply_text("❌ Failed to run speed test. Please try again later.")

async def speedtest_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run detailed speed test with server info."""
    try:
        msg = await update.message.reply_text("⏳ Running advanced speed test... This may take a minute")
        
        st = speedtest.Speedtest()
        st.get_best_server()
        
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        ping = st.results.ping
        server = st.results.server['sponsor']
        country = st.results.server['country']
        isp = st.results.client['isp']
        ip = st.results.client['ip']
        
        result = (
            "📊 *Advanced SpeedTest Results*\n\n"
            f"🌍 *Server:* `{escape_markdown_v2(server)} ({escape_markdown_v2(country)})`\n"
            f"🏠 *ISP:* `{escape_markdown_v2(isp)}`\n"
            f"📡 *IP:* `{ip}`\n\n"
            f"⬇️ *Download:* `{download:.2f} Mbps`\n"
            f"⬆️ *Upload:* `{upload:.2f} Mbps`\n"
            f"🏓 *Ping:* `{ping:.2f} ms`"
        )
        
        await msg.edit_text(result, parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Error in speedtest_advanced command: {e}")
        await update.message.reply_text("❌ Failed to run advanced speed test. Please try again later.")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping a specified host."""
    if not context.args:
        await update.message.reply_text("Please specify a host to ping. Example: /ping google.com")
        return
    
    host = context.args[0]
    try:
        msg = await update.message.reply_text(f"⏳ Pinging {host}...")
        
        # Cross-platform ping command
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '4', host]
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        
        if stderr:
            await msg.edit_text(f"❌ Error pinging {host}:\n{stderr}")
            return
        
        # Extract ping statistics
        stats = re.findall(r'(\d+\.?\d*) ms', stdout)
        if stats:
            min_ping = stats[-3] if len(stats) >= 3 else "N/A"
            avg_ping = stats[-2] if len(stats) >= 2 else "N/A"
            max_ping = stats[-1] if len(stats) >= 1 else "N/A"
            
            result = (
                f"📶 *Ping Results for {escape_markdown_v2(host)}*\n\n"
                f"🏓 *Min:* `{min_ping} ms`\n"
                f"📊 *Avg:* `{avg_ping} ms`\n"
                f"🚀 *Max:* `{max_ping} ms`"
            )
            await msg.edit_text(result, parse_mode='MarkdownV2')
        else:
            await msg.edit_text(f"⚠️ Could not parse ping results for {host}:\n\n`{stdout}`", parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        await update.message.reply_text(f"❌ Failed to ping {host}. Please try again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error: {context.error}", exc_info=True)
    
    if update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred while processing your request. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("speedtest", speedtest_command))
    application.add_handler(CommandHandler("speedtest_advanced", speedtest_advanced))
    application.add_handler(CommandHandler("ping", ping_command))

    # Register error handler
    application.add_error_handler(error_handler)

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()