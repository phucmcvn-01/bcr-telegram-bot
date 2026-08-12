        import logging
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Tạo Web Server đơn giản bằng Flask cho Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot BCR is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# 2. Cấu hình Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_data = {}

# 3. Thuật toán xử lý chuỗi BCR
def analyze_bcr(history: str) -> str:
    tokens = [c.upper() for c in history.replace(" ", "") if c.upper() in ['P', 'B', 'T']]
    
    if not tokens:
        return "⚠️ Chuỗi dữ liệu không hợp lệ. Vui lòng chỉ nhập B (Banker), P (Player) hoặc T (Tie)."

    total = len(tokens)
    p_count = tokens.count('P')
    b_count = tokens.count('B')
    t_count = tokens.count('T')

    p_rate = round((p_count / total) * 100, 1)
    b_rate = round((b_count / total) * 100, 1)
    t_rate = round((t_count / total) * 100, 1)

    last_symbol = tokens[-1]
    streak = 0
    for item in reversed(tokens):
        if item == last_symbol:
            streak += 1
        else:
            break

    if streak >= 4:
        prediction = last_symbol
        reason = f"Phát hiện cầu Bệt {last_symbol} ({streak} tay liên tiếp). Khuyến nghị đi theo cầu."
    elif streak == 1:
        prediction = 'B' if last_symbol == 'P' else 'P'
        reason = "Dự đoán cầu Xen kẽ (1-1)."
    else:
        prediction = 'B' if b_count <= p_count else 'P'
        reason = f"Cân bằng xác suất (Tỷ lệ hiện tại - B: {b_rate}% | P: {p_rate}%)."

    name_map = {'B': '🔴 BANKER', 'P': '🔵 PLAYER', 'T': '🟢 TIE'}

    return (
        f"📊 **KẾT QUẢ PHÂN TÍCH BCR**\n"
        f"-------------------------------\n"
        f"🔹 **Tổng số ván:** {total}\n"
        f"🔴 **Banker:** {b_count} ({b_rate}%)\n"
        f"🔵 **Player:** {p_count} ({p_rate}%)\n"
        f"🟢 **Tie:** {t_count} ({t_rate}%)\n\n"
        f"🔥 **Cầu hiện tại:** {name_map[last_symbol]} bệt {streak} tay.\n"
        f"-------------------------------\n"
        f"💡 **DỰ ĐOÁN VÁN TẾP THEO:** {name_map[prediction]}\n"
        f"📌 *Cơ sở:* {reason}"
    )

# 4. Các lệnh Telegram Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Chào mừng bạn đến với BCR Analytics Bot!**\n\n"
        "Hướng dẫn sử dụng:\n"
        "- Gửi chuỗi kết quả ván đấu, ví dụ: `P B P P B B B` hoặc `P B T P B`\n"
        "- Bot sẽ tự động thống kê và đưa ra dự đoán ván tiếp theo.\n"
        "- Dùng lệnh /clear để xóa lịch sử."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text("🗑️ Đã xóa lịch sử ván đấu của bạn.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = analyze_bcr(text)
    await update.message.reply_text(response, parse_mode='Markdown')

# 5. Khởi chạy song song Flask Server và Telegram Bot
if __name__ == '__main__':
    # Chạy Web Server trên một luồng riêng
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    # Chạy Telegram Bot
    BOT_TOKEN = "8960157189:AAExpczWz8zTNJZo0ApGq_pt-v2INRV4XII"
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
