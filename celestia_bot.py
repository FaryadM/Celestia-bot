import os
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- ذخیره اکانت‌ها (فایل JSON) ----------
ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

# ---------- کیبوردها ----------
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

def back_to_profile_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile")]]
    return InlineKeyboardMarkup(keyboard)

def adventure_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗡 شروع ماجراجویی", callback_data="adventure_start")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def no_account_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ ساخت اکانت", callback_data="create_account")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def delete_confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ مطمئنم", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ پشیمون شدم", callback_data="profile")],
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
    
    user_id = str(query.from_user.id)
    accounts = load_accounts()

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
        if user_id not in accounts:
            await query.edit_message_text(
                "👤 *پروفایل*\n\n"
                "❌ هنوز هیچ اکانتی نساختی!\n\n"
                "برای شروع ماجراجویی، اول یه اکانت بساز:",
                reply_markup=no_account_keyboard(),
                parse_mode="Markdown",
            )
        else:
            acc = accounts[user_id]
            name = acc.get("name", "بی‌نام")
            level = acc.get("level", 1)
            xp = acc.get("xp", 0)
            skills = acc.get("skills", ["بدون مهارت"])
            
            skills_text = "، ".join(skills) if isinstance(skills, list) else skills
            
            await query.edit_message_text(
                f"👤 *پروفایل {name}*\n\n"
                f"🎚 سطح: `{level}`\n"
                f"✨ تجربه: `{xp} XP`\n"
                f"⚔️ مهارت‌ها: {skills_text}",
                reply_markup=profile_keyboard(),
                parse_mode="Markdown",
            )

    elif data == "create_account":
        name = query.from_user.first_name or "بازیکن"
        accounts[user_id] = {
            "name": name,
            "level": 1,
            "xp": 0,
            "skills": ["تازه‌کار"],
        }
        save_accounts(accounts)
        
        await query.edit_message_text(
            f"✅ اکانت `{name}` ساخته شد!\n\n"
            f"خوش اومدی به دنیای سلستیا 🌌",
            reply_markup=back_to_profile_keyboard(),
            parse_mode="Markdown",
        )

    elif data == "delete_account":
        if user_id not in accounts:
            await query.edit_message_text(
                "❌ اکانتی نداری که بخوای حذف کنی!",
                reply_markup=back_keyboard(),
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(
                "⚠️ *مطمئنی می‌خوای اکانتت حذف بشه؟*\n\n"
                "اگه حذف کنی، همه اطلاعاتت از دست میره "
                "و دیگه نمی‌تونی برشون گردونی!",
                reply_markup=delete_confirm_keyboard(),
                parse_mode="Markdown",
            )

    elif data == "confirm_delete":
        if user_id not in accounts:
            await query.edit_message_text(
                "❌ اکانتی نداری!",
                reply_markup=back_keyboard(),
                parse_mode="Markdown",
            )
        else:
            # ساخت کد ۵ رقمی رندوم
            code = str(random.randint(10000, 99999))
            context.user_data["delete_code"] = code
            context.user_data["waiting_for_code"] = True
            
            await query.edit_message_text(
                f"🔐 برای تأیید حذف، این کد رو کپی کن و بفرست:\n\n"
                f"👉 `{code}` 👈\n\n"
                f"⏰ این کد فقط ۳ دقیقه اعتبار داره.",
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

# ---------- مدیریت پیام‌های متنی (برای دریافت کد تأیید) ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    
    # اگه منتظر کد تأیید هستیم
    if context.user_data.get("waiting_for_code"):
        user_code = update.message.text.strip()
        correct_code = context.user_data.get("delete_code")
        
        if user_code == correct_code:
            # حذف اکانت
            accounts = load_accounts()
            if user_id in accounts:
                del accounts[user_id]
                save_accounts(accounts)
            
            context.user_data["waiting_for_code"] = False
            context.user_data["delete_code"] = None
            
            await update.message.reply_text(
                "✅ اکانتت با موفقیت حذف شد.\n\n"
                "هر وقت خواستی برگردی، می‌تونی یه اکانت جدید بسازی 🌌",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                "❌ کد اشتباهه! دوباره تلاش کن یا بازگشت بزن.",
                reply_markup=delete_confirm_keyboard(),
            )
    else:
        # اگه پیام معمولی بود، منوی اصلی رو نشون بده
        await update.message.reply_text(
            "از دکمه‌ها استفاده کن 👇",
            reply_markup=main_menu_keyboard(),
        )

def main():
    TOKEN = os.environ.get("TOKEN")
    
    if not TOKEN:
        print("❌ خطا: متغیر TOKEN تنظیم نشده!")
        print("برو توی Railway → Variables و TOKEN رو اضافه کن")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🌌 ربات سلستیا روشن شد…")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
