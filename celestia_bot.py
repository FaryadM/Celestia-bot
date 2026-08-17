from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------- دکمه‌های ثابت ----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
        [InlineKeyboardButton("⚔️ ماجراجویی", callback_data="adventure")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    return InlineKeyboardMarkup(keyboard)

def adventure_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗡 شروع ماجراجویی", callback_data="adventure_start")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌌 به دنیای سلستیا خوش اومدی!\n"
        "دنیای شمشیر و جادو در انتظار توئه…\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:"
    )
    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

# ---------- مدیریت کلیک روی دکمه‌ها ----------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        text = (
            "🌌 به دنیای سلستیا خوش اومدی!\n"
            "دنیای شمشیر و جادو در انتظار توئه…\n\n"
            "یکی از گزینه‌های زیر رو انتخاب کن:"
        )
        await query.edit_message_text(
            text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown",
        )

    elif data == "profile":
        await query.edit_message_text(
            "👤 پروفایل\n\nیکی از گزینه‌های زیر انتخاب کن:",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )

    elif data == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات\n\nیکی از گزینه‌های زیر انتخاب کن:",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )

    elif data == "adventure":
        await query.edit_message_text(
            "⚔️ ماجراجویی\n\nیکی از گزینه‌های زیر انتخاب کن:",
            reply_markup=adventure_keyboard(),
            parse_mode="Markdown",
        )

    elif data == "adventure_start":
        await query.edit_message_text(
            "🗡 شروع ماجراجویی\n\n"
            "گام نخست… (اینجا قراره مرحله‌ی اول داستان بیاد)",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )
def main():
    TOKEN = "8818132213:AAGyLWfZCtYj0LQNt7VBQlPTf1mSHrRhgEk"  # توکن رباتت رو از BotFather بگیر
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("ربات سلستیا روشن شد…")
    app.run_polling()

main()