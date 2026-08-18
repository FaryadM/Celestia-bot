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

# ========== تنظیمات ==========
# آیدی کانال (مثلاً @mychannel رو بذار)
CHANNEL_USERNAME = "@Celestia_world1"  # ⚠️ اینو عوض کن
# اگه کانالت خصوصیه، بجای یوزرنیم، آیدی عددی بذار (مثلاً -1001234567890)

# ---------- ذخیره اکانت‌ها ----------
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

# ---------- چک عضویت در کانال ----------
async def check_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # وضعیت‌های مجاز: creator, administrator, member
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        print(f"⚠️ خطا در چک عضویت: {e}")
        # اگه خطا داد، فرض می‌کنیم عضو نیست
        return False

def force_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 عضو کانال میشم", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")],
    ]
    return InlineKeyboardMarkup(keyboard)

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
    user_id = update.message.from_user.id
    
    # چک عضویت
    is_member = await check_membership(context, user_id)
    if not is_member:
        await update.message.reply_text(
            "👋 سلام!\n\n"
            "برای استفاده از ربات سلستیا، اول باید عضو کانال ما بشی 🌌\n\n"
            "روی دکمه پایین بزن و بعدش دکمه «عضو شدم» رو بزن:",
            reply_markup=force_join_keyboard(),
        )
        return
    
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
    
    user_id = query.from_user.id
    accounts = load_accounts()
    
    # 🔒 چک عضویت برای همه دکمه‌ها (به جز خود join check)
    if data != "check_join":
        is_member = await check_membership(context, user_id)
        if not is_member:
            await query.edit_message_text(
                "⚠️ هنوز عضو کانال نشدی!\n\n"
                "اول عضو کانال شو، بعد بیا:",
                reply_markup=force_join_keyboard(),
            )
            return

    # ---------- چک عضویت: کاربر زد "عضو شدم" ----------
    if data == "check_join":
        is_member = await check_membership(context, user_id)
        if is_member:
            text = (
                "✅ عالی! عضو شدی.\n\n"
                "🌌 به دنیای سلستیا خوش اومدی!\n"
                "دنیای شمشیر و جادو در انتظار توئه…\n\n"
                "یکی از گزینه‌های زیر رو انتخاب کن:"
            )
            await query.edit_message_text(
                text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown",
            )
        else:
            await query.answer("❌ هنوز عضو نشدی! اول عضو شو.", show_alert=True)
        return

    # ---------- بقیه دکمه‌ها ----------
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
        if str(user_id) not in accounts:
            await query.edit_message_text(
                "👤 *پروفایل*\n\n"
                "❌ هنوز هیچ اکانتی نساختی!\n\n"
                "برای شروع ماجراجویی، اول یه اکانت بساز:",
                reply_markup=no_account_keyboard(),
                parse_mode="Markdown",
            )
        else:
            acc = accounts[str(user_id)]
            name = acc.get("name", "بی‌نام")
            level = acc.get("level", 1)
            xp = acc.get("xp", 0)
            skills = acc.get("skills", ["بدون مهارت"])
            telegram_id = acc.get("telegram_id", user_id)
            
            skills_text = "، ".join(skills) if isinstance(skills, list) else skills
            
            await query.edit_message_text(
                f"👤 *پروفایل {name}*\n\n"
                f"🆔 آیدی: `{telegram_id}`\n"
                f"🎚 سطح: `{level}`\n"
                f"✨ تجربه: `{xp} XP`\n"
                f"⚔️ مهارت‌ها: {skills_text}",
                reply_markup=profile_keyboard(),
                parse_mode="Markdown",
            )

    elif data == "create_account":
        name = query.from_user.first_name or "بازیکن"
        accounts[str(user_id)] = {
            "telegram_id": user_id,
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
        if str(user_id) not in accounts:
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
        if str(user_id) not in accounts:
            await query.edit_message_text(
                "❌ اکانتی نداری!",
                reply_markup=back_keyboard(),
                parse_mode="Markdown",
            )
        else:
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

# ---------- مدیریت پیام‌های متنی ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    
    # چک عضویت برای پیام‌های معمولی هم
    is_member = await check_membership(context, int(user_id))
    if not is_member:
        await update.message.reply_text(
            "⚠️ اول باید عضو کانال بشی:",
            reply_markup=force_join_keyboard(),
        )
        return
    
    if context.user_data.get("waiting_for_code"):
        user_code = update.message.text.strip()
        correct_code = context.user_data.get("delete_code")
        
        if user_code == correct_code:
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
        await update.message.reply_text(
            "از دکمه‌ها استفاده کن 👇",
            reply_markup=main_menu_keyboard(),
        )

def main():
    TOKEN = os.environ.get("TOKEN")
    
    if not TOKEN:
        print("❌ خطا: متغیر TOKEN تنظیم نشده!")
        return
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🌌 ربات سلستیا روشن شد…")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
