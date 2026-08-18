import os
import json
import time
import secrets
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError, BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# تنظیمات اصلی
# =========================================================

CHANNEL_USERNAME = "@Celestia_world1"

ACCOUNTS_FILE = "accounts.json"

# =========================================================
# اطلاعات ورود پنل مدیریت
# =========================================================

CREATOR_USERNAME = "Faryad"
CREATOR_PASSWORD = "Faryad105510M"

ADMIN_USERNAME = "Amir"
ADMIN_PASSWORD = "Admin1099"

# مدت اعتبار کد حذف اکانت
DELETE_CODE_EXPIRE_SECONDS = 180


# =========================================================
# تنظیمات لاگ
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# مدیریت فایل اکانت‌ها
# =========================================================

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, dict):
                return data

            return {}

    except (json.JSONDecodeError, OSError) as error:
        logger.error("خطا در خواندن accounts.json: %s", error)
        return {}


def save_accounts(accounts):
    try:
        temp_file = ACCOUNTS_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(
                accounts,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(temp_file, ACCOUNTS_FILE)

    except OSError as error:
        logger.error("خطا در ذخیره accounts.json: %s", error)


# =========================================================
# توابع کمکی
# =========================================================

def get_account(accounts, user_id):
    return accounts.get(str(user_id))


def is_creator(context):
    return context.user_data.get("management_role") == "creator"


def is_admin(context):
    return context.user_data.get("management_role") == "admin"


def is_management_user(context):
    return context.user_data.get("management_role") in {
        "creator",
        "admin",
    }


def clear_management_session(context):
    context.user_data.pop("management_role", None)
    context.user_data.pop("management_login_step", None)
    context.user_data.pop("management_username", None)


# =========================================================
# ارسال پیام با توجه به تنظیم اعلان کاربر
# =========================================================

async def send_user_message(
    context,
    user_id,
    text,
    reply_markup=None,
    parse_mode=None,
):
    accounts = load_accounts()

    account = accounts.get(str(user_id), {})

    notifications_enabled = account.get(
        "notifications",
        True,
    )

    try:
        return await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_notification=not notifications_enabled,
        )

    except TelegramError as error:
        logger.error(
            "خطا در ارسال پیام به %s: %s",
            user_id,
            error,
        )

        return None


# =========================================================
# بررسی عضویت کانال
# =========================================================

async def check_membership(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:

    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )

        return member.status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        }

    except TelegramError as error:
        logger.warning(
            "خطا در بررسی عضویت کاربر %s: %s",
            user_id,
            error,
        )

        return False


# =========================================================
# کیبورد عضویت کانال
# =========================================================

def force_join_keyboard():

    channel_link = (
        f"https://t.me/"
        f"{CHANNEL_USERNAME.replace('@', '')}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=channel_link,
            )
        ],
        [
            InlineKeyboardButton(
                "✅ عضو شدم",
                callback_data="check_join",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# منوی اصلی
# =========================================================

def main_menu_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 پروفایل",
                callback_data="profile",
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings",
            )
        ],
        [
            InlineKeyboardButton(
                "⚔️ ماجراجویی",
                callback_data="adventure",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back_main",
                )
            ]
        ]
    )


def back_to_profile_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت به پروفایل",
                    callback_data="profile",
                )
            ]
        ]
    )


# =========================================================
# ماجراجویی
# =========================================================

def adventure_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "🗡 شروع ماجراجویی",
                callback_data="adventure_start",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back_main",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# پروفایل
# =========================================================

def no_account_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ ساخت اکانت",
                callback_data="create_account",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به خانه",
                callback_data="back_main",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def profile_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "🗑 حذف اکانت",
                callback_data="delete_account",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به خانه",
                callback_data="back_main",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def delete_confirm_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ مطمئنم",
                callback_data="confirm_delete",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ پشیمون شدم",
                callback_data="profile",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# تنظیمات کاربر
# =========================================================

def settings_keyboard(account):

    notifications = account.get(
        "notifications",
        True,
    )

    if notifications:
        notification_text = "🔴 اعلان‌ها خاموش"
    else:
        notification_text = "🟢 اعلان‌ها روشن"

    keyboard = [
        [
            InlineKeyboardButton(
                notification_text,
                callback_data="toggle_notifications",
            )
        ],
        [
            InlineKeyboardButton(
                "🛡 ورود به اتاق مدیریت و کنترل",
                callback_data="management_room",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به خانه",
                callback_data="back_main",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# اتاق مدیریت
# =========================================================

def management_room_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "👑 اتاق سازنده",
                callback_data="creator_room",
            )
        ],
        [
            InlineKeyboardButton(
                "🛡 اتاق ادمین‌ها",
                callback_data="admin_room",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به تنظیمات",
                callback_data="settings",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# پنل سازنده
# =========================================================

def creator_panel_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                "👥 مشاهده کاربران",
                callback_data="creator_users",
            )
        ],
        [
            InlineKeyboardButton(
                "🔐 تغییر رمز سازنده",
                callback_data="change_creator_password",
            )
        ],
        [
            InlineKeyboardButton(
                "🚪 خروج از پنل",
                callback_data="management_logout",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def creator_users_keyboard(accounts):

    keyboard = []

    for user_id, account in accounts.items():

        name = account.get(
            "name",
            "بی‌نام",
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"👤 {name} | {user_id}",
                    callback_data=f"creator_user:{user_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت به اتاق سازنده",
                callback_data="creator_room",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# مدیریت آیتم و سکه
# =========================================================

def creator_user_keyboard(user_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "🎁 افزودن هدیه",
                callback_data=f"give_gift:{user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🪙 افزودن سکه",
                callback_data=f"add_coins:{user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🎒 افزودن آیتم",
                callback_data=f"add_item:{user_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت به کاربران",
                callback_data="creator_users",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# /start
# ======================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    user_id = update.message.from_user.id

    is_member = await check_membership(
        context,
        user_id,
    )

    if not is_member:

        await update.message.reply_text(
            "👋 سلام!\n\n"
            "برای استفاده از ربات سلستیا، "
            "اول باید عضو کانال ما بشی 🌌\n\n"
            "بعد از عضویت روی «عضو شدم» بزن.",
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
    )


# =========================================================
# ورود به پنل مدیریت
# =========================================================

async def start_management_login(
    query,
    context,
):

    context.user_data["management_login_step"] = "username"
    context.user_data.pop("management_username", None)

    await query.edit_message_text(
        "🛡 اتاق مدیریت و کنترل\n\n"
        "این بخش فقط مختص سازنده و ادمین‌های ربات است.\n\n"
        "برای ورود، ابتدا نام کاربری مخصوص خود را ارسال کن:"
    )


# =========================================================
# مدیریت کلیک دکمه‌ها
# =========================================================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data
    user_id = query.from_user.id

    try:
        await query.answer()
    except TelegramError:
        pass

    # =====================================================
    # بررسی عضویت
    # =====================================================

    if data != "check_join":

        is_member = await check_membership(
            context,
            user_id,
        )

        if not is_member:

            try:
                await query.edit_message_text(
                    "⚠️ هنوز عضو کانال نشدی!\n\n"
                    "اول عضو کانال شو و بعد دوباره تلاش کن.",
                    reply_markup=force_join_keyboard(),
                )
            except BadRequest:
                pass

            return

    # =====================================================
    # عضو شدم
    # =====================================================

    if data == "check_join":

        is_member = await check_membership(
            context,
            user_id,
        )

        if is_member:

            await query.edit_message_text(
                "✅ عالی! عضو شدی.\n\n"
                "🌌 به دنیای سلستیا خوش اومدی!\n"
                "دنیای شمشیر و جادو در انتظار توئه…\n\n"
                "یکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=main_menu_keyboard(),
            )

        else:

            await query.answer(
                "❌ هنوز عضو کانال نشدی!",
                show_alert=True,
            )

        return

    accounts = load_accounts()
    user_key = str(user_id)

    # =====================================================
    # خانه
    # =====================================================

    if data == "back_main":

        await query.edit_message_text(
            "🌌 به دنیای سلستیا خوش اومدی!\n"
            "دنیای شمشیر و جادو در انتظار توئه…\n\n"
            "یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=main_menu_keyboard(),
        )

        return

    # =====================================================
    # پروفایل
    # =====================================================

    if data == "profile":

        if user_key not in accounts:

            await query.edit_message_text(
                "👤 پروفایل\n\n"
                "❌ هنوز هیچ اکانتی نساختی!\n\n"
                "برای شروع ماجراجویی، اول یه اکانت بساز:",
                reply_markup=no_account_keyboard(),
            )

        else:

            acc = accounts[user_key]

            name = acc.get(
                "name",
                "بی‌نام",
            )

            level = acc.get(
                "level",
                1,
            )

            xp = acc.get(
                "xp",
                0,
            )

            skills = acc.get(
                "skills",
                ["تازه‌کار"],
            )

            telegram_id = acc.get(
                "telegram_id",
                user_id,
            )

            coins = acc.get(
                "coins",
                0,
            )

            items = acc.get(
                "items",
                [],
            )

            skills_text = (
                "، ".join(skills)
                if isinstance(skills, list)
                else str(skills)
            )

            await query.edit_message_text(
                f"👤 پروفایل {name}\n\n"
                f"🆔 آیدی: `{telegram_id}`\n"
                f"🎚 سطح: `{level}`\n"
                f"✨ تجربه: `{xp} XP`\n"
                f"🪙 سکه: `{coins}`\n"
                f"🎒 تعداد آیتم‌ها: `{len(items)}`\n"
                f"⚔️ مهارت‌ها: {skills_text}",
                reply_markup=profile_keyboard(),
                parse_mode="Markdown",
            )

        return

    # =====================================================
    # ساخت اکانت
    # =====================================================

    if data == "create_account":

        if user_key in accounts:

            await query.answer(
                "❌ تو قبلاً اکانت ساخته‌ای.",
                show_alert=True,
            )

            return

        name = (
            query.from_user.first_name
            or "بازیکن"
        )

        accounts[user_key] = {
            "telegram_id": user_id,
            "name": name,
            "level": 1,
            "xp": 0,
            "coins": 0,
            "skills": ["تازه‌کار"],
            "items": [],
            "notifications": True,
            "created_at": int(time.time()),
        }

        save_accounts(accounts)

        await query.edit_message_text(
            f"✅ اکانت `{name}` ساخته شد!\n\n"
            "🌌 خوش اومدی به دنیای سلستیا.",
            reply_markup=back_to_profile_keyboard(),
            parse_mode="Markdown",
        )

        return

    # =====================================================
    # حذف اکانت
    # =====================================================

    if data == "delete_account":

        if user_key not in accounts:

            await query.edit_message_text(
                "❌ اکانتی نداری که بخوای حذف کنی!",
                reply_markup=back_keyboard(),
            )

        else:

            await query.edit_message_text(
                "⚠️ مطمئنی می‌خوای اکانتت حذف بشه؟\n\n"
                "اگه حذف کنی، همه اطلاعاتت از دست میره "
                "و دیگه نمی‌تونی برشون گردونی!",
                reply_markup=delete_confirm_keyboard(),
            )

        return

    # =====================================================
    # تأیید حذف
    # =====================================================

    if data == "confirm_delete":

        if user_key not in accounts:

            await query.edit_message_text(
                "❌ اکانتی نداری!",
                reply_markup=back_keyboard(),
            )

            return

        code = str(
            secrets.randbelow(90000) + 10000
        )

        context.user_data["delete_code"] = code
        context.user_data["delete_expires"] = (
            time.time()
            + DELETE_CODE_EXPIRE_SECONDS
        )
        context.user_data["waiting_for_code"] = True

        await query.edit_message_text(
            "🔐 برای تأیید حذف اکانت، "
            "کد زیر را برای ربات ارسال کن:\n\n"
            f"👉 `{code}` 👈\n\n"
            "⏰ این کد فقط ۳ دقیقه اعتبار دارد.",
            parse_mode="Markdown",
        )

        return

    # =====================================================
    # تنظیمات
    # =====================================================

    if data == "settings":

        account = accounts.get(user_key)

        if not account:

            await query.edit_message_text(
                "❌ ابتدا باید اکانت بسازی.",
                reply_markup=no_account_keyboard(),
            )

            return

        await query.edit_message_text(
            "⚙️ تنظیمات\n\n"
            "تنظیمات موردنظر خودت را انتخاب کن:",
            reply_markup=settings_keyboard(account),
        )

        return

    # =====================================================
    # روشن / خاموش کردن اعلان
    # =====================================================

    if data == "toggle_notifications":

        if user_key not in accounts:

            await query.answer(
                "❌ ابتدا اکانت بساز.",
                show_alert=True,
            )

            return

        current = accounts[user_key].get(
            "notifications",
            True,
        )

        accounts[user_key]["notifications"] = not current

        save_accounts(accounts)

        account = accounts[user_key]

        if account["notifications"]:

            message = (
                "🟢 اعلان‌ها روشن شد.\n\n"
                "از این به بعد پیام‌های ربات "
                "به صورت عادی اعلان خواهند داشت."
            )

        else:

            message = (
                "🔴 اعلان‌ها خاموش شد.\n\n"
                "پیام‌های ربات همچنان برایت ارسال می‌شوند، "
                "اما به صورت بی‌صدا خواهند بود."
            )

        await query.edit_message_text(
            message,
            reply_markup=settings_keyboard(account),
        )

        return

    # =====================================================
    # اتاق مدیریت
    # =====================================================

    if data == "management_room":

        await start_management_login(
            query,
            context,
        )

        return

    # =====================================================
    # اتاق سازنده
    # =====================================================

    if data == "creator_room":

        if not is_creator(context):

            await query.answer(
                "❌ دسترسی سازنده ندارید.",
                show_alert=True,
            )

            return

        await query.edit_message_text(
            "👑 اتاق سازنده\n\n"
            "به پنل اختصاصی سازنده سلستیا خوش آمدی.\n\n"
            "از این بخش می‌توانی کاربران و اطلاعات "
            "اکانت آن‌ها را مدیریت کنی.",
            reply_markup=creator_panel_keyboard(),
        )

        return

    # =====================================================
    # اتاق ادمین
    # =====================================================

    if data == "admin_room":

        await query.edit_message_text(
            "🛡 اتاق ادمین‌ها\n\n"
            "⏳ این بخش فعلاً فعال نشده است.",
            reply_markup=management_room_keyboard(),
        )

        return

    # =====================================================
    # مشاهده کاربران
    # =====================================================

    if data == "creator_users":

        if not is_creator(context):

            await query.answer(
                "❌ دسترسی ندارید.",
                show_alert=True,
            )

            return

        if not accounts:

            await query.edit_message_text(
                "👥 کاربران ربات\n\n"
                "فعلاً هیچ کاربری اکانت نساخته است.",
                reply_markup=creator_panel_keyboard(),
            )

            return

        await query.edit_message_text(
            f"👥 کاربران ربات\n\n"
            f"تعداد اکانت‌ها: {len(accounts)}\n\n"
            "برای مشاهده پروفایل، روی کاربر موردنظر بزن:",
            reply_markup=creator_users_keyboard(accounts),
        )

        return

    # =====================================================
    # مشاهده پروفایل یک کاربر توسط سازنده
    # =====================================================

    if data.startswith("creator_user:"):

        if not is_creator(context):

            await query.answer(
                "❌ دسترسی ندارید.",
                show_alert=True,
            )

            return

        target_id = data.split(":", 1)[1]

        account = accounts.get(target_id)

        if not account:

            await query.answer(
                "❌ این اکانت پیدا نشد.",
                show_alert=True,
            )

            return

        name = account.get(
            "name",
            "بی‌نام",
        )

        level = account.get(
            "level",
            1,
        )

        xp = account.get(
            "xp",
            0,
        )

        coins = account.get(
            "coins",
            0,
        )

        items = account.get(
            "items",
            [],
        )

        skills = account.get(
            "skills",
            [],
        )

        await query.edit_message_text(
            "👤 پروفایل بازیکن\n\n"
            f"👤 نام: {name}\n"
            f"🆔 Telegram ID: `{target_id}`\n"
            f"🎚 سطح: `{level}`\n"
            f"✨ XP: `{xp}`\n"
            f"🪙 سکه: `{coins}`\n"
            f"🎒 آیتم‌ها: `{len(items)}`\n"
            f"⚔️ مهارت‌ها: {', '.join(skills)}",
            reply_markup=creator_user_keyboard(target_id),
            parse_mode="Markdown",
        )

        return

    # =====================================================
    # افزودن سکه
    # =====================================================

    if data.startswith("add_coins:"):

        if not is_creator(context):

            await query.answer(
                "❌ فقط سازنده دسترسی دارد.",
                show_alert=True,
            )

            return

        target_id = data.split(":", 1)[1]

        if target_id not in accounts:

            await query.answer(
                "❌ کاربر پیدا نشد.",
                show_alert=True,
            )

            return

        context.user_data["creator_action"] = "add_coins"
        context.user_data["target_user_id"] = target_id

        await query.edit_message_text(
            "🪙 افزودن سکه\n\n"
            "مقدار سکه‌ای که می‌خواهی به کاربر بدهی را ارسال کن:\n\n"
            "مثال:\n"
            "`1000`\n"
            "`50000`\n"
            "`999999999`",
            parse_mode="Markdown",
        )

        return

    # =====================================================
    # افزودن آیتم
    # =====================================================

    if data.startswith("add_item:"):

        if not is_creator(context):

            await query.answer(
                "❌ فقط سازنده دسترسی دارد.",
                show_alert=True,
            )

            return

        target_id = data.split(":", 1)[1]

        if target_id not in accounts:

            await query.answer(
                "❌ کاربر پیدا نشد.",
                show_alert=True,
            )

            return

        context.user_data["creator_action"] = "add_item"
        context.user_data["target_user_id"] = target_id

        await query.edit_message_text(
            "🎒 افزودن آیتم\n\n"
            "نام آیتمی که می‌خواهی به بازیکن بدهی را ارسال کن:"
        )

        return

    # =====================================================
    # هدیه
    # =====================================================

    if data.startswith("give_gift:"):

        if not is_creator(context):

            await query.answer(
                "❌ فقط سازنده دسترسی دارد.",
                show_alert=True,
            )

            return

        target_id = data.split(":", 1)[1]

        if target_id not in accounts:

            await query.answer(
                "❌ کاربر پیدا نشد.",
                show_alert=True,
            )

            return

        context.user_data["creator_action"] = "give_gift"
        context.user_data["target_user_id"] = target_id

        await query.edit_message_text(
            "🎁 ارسال هدیه\n\n"
            "نام هدیه یا آیتمی که می‌خواهی به بازیکن بدهی را ارسال کن:"
        )

        return

    # =====================================================
    # تغییر رمز سازنده
    # =====================================================

    if data == "change_creator_password":

        if not is_creator(context):

            await query.answer(
                "❌ فقط سازنده دسترسی دارد.",
           
               show_alert=True,
            )

            return

        await query.edit_message_text(
            "🔐 تغییر رمز سازنده\n\n"
            "در این نسخه رمز اصلی داخل تنظیمات کد قرار دارد.\n\n"
            "برای تغییر رمز، مقدار زیر را در ابتدای فایل تغییر بده:\n\n"
            "CREATOR_PASSWORD = \"رمز جدید\"\n\n"
            "این بخش را عمداً از داخل تلگرام قابل تغییر نکردم "
            "تا رمز اصلی از طریق یک پیام ناخواسته قابل تغییر نباشد.",
            reply_markup=creator_panel_keyboard(),
        )

        return

    # =====================================================
    # خروج
    # =====================================================

    if data == "management_logout":

        clear_management_session(context)

        await query.edit_message_text(
            "🚪 با موفقیت از اتاق مدیریت خارج شدی.",
            reply_markup=main_menu_keyboard(),
        )

        return

    # =====================================================
    # شروع ماجراجویی
    # =====================================================

    if data == "adventure":

        if user_key not in accounts:

            await query.edit_message_text(
                "⚔️ ماجراجویی\n\n"
                "❌ برای شروع ماجراجویی ابتدا باید اکانت بسازی.",
                reply_markup=no_account_keyboard(),
            )

            return

        await query.edit_message_text(
            "⚔️ ماجراجویی\n\n"
            "یکی از گزینه‌های زیر را انتخاب کن:",
            reply_markup=adventure_keyboard(),
        )

        return

    if data == "adventure_start":

        if user_key not in accounts:

            await query.edit_message_text(
                "❌ ابتدا باید اکانت بسازی.",
                reply_markup=no_account_keyboard(),
            )

            return

        await query.edit_message_text(
            "🗡 شروع ماجراجویی\n\n"
            "گام نخست…\n\n"
            "🌌 داستان سلستیا از اینجا شروع می‌شود.\n"
            "سیستم مراحل و مبارزات در ادامه به این بخش اضافه خواهد شد.",
            reply_markup=back_keyboard(),
        )

        return


# =========================================================
# مدیریت پیام‌های متنی
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    user_id = update.message.from_user.id
    user_key = str(user_id)

    text = update.message.text.strip()

    # =====================================================
    # بررسی عضویت
    # =====================================================

    is_member = await check_membership(
        context,
        user_id,
    )

    if not is_member:

        await update.message.reply_text(
            "⚠️ اول باید عضو کانال بشی:",
            reply_markup=force_join_keyboard(),
        )

        return

    # =====================================================
    # ورود به پنل مدیریت - نام کاربری
    # =====================================================

    login_step = context.user_data.get(
        "management_login_step"
    )

    if login_step == "username":

        context.user_data["management_username"] = text
        context.user_data["management_login_step"] = "password"

        await update.message.reply_text(
            "🔐 حالا رمز ورود را ارسال کن:"
        )

        return

    # =====================================================
    # ورود به پنل مدیریت - رمز
    # =====================================================

    if login_step == "password":

        username = context.user_data.get(
            "management_username"
        )

        password = text

        if (
            username == CREATOR_USERNAME
            and password == CREATOR_PASSWORD
        ):

            context.user_data["management_role"] = "creator"

            context.user_data.pop(
                "management_login_step",
                None,
            )

            context.user_data.pop(
                "management_username",
                None,
            )

            await update.message.reply_text(
                "👑 ورود موفق بود!\n\n"
                "به اتاق سازنده سلستیا خوش آمدی.",
                reply_markup=creator_panel_keyboard(),
            )

            return

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            context.user_data["management_role"] = "admin"

            context.user_data.pop(
                "management_login_step",
                None,
            )

            context.user_data.pop(
                "management_username",
                None,
            )

            await update.message.reply_text(
                "🛡 ورود موفق بود!\n\n"
                "اتاق ادمین‌ها فعلاً فعال نشده است.",
                reply_markup=management_room_keyboard(),
            )

            return

        context.user_data.pop(
            "management_login_step",
            None,
        )

        context.user_data.pop(
            "management_username",
            None,
        )

        await update.message.reply_text(
            "❌ نام کاربری یا رمز عبور اشتباه است.\n\n"
            "برای ورود دوباره از بخش تنظیمات اقدام کن.",
            reply_markup=main_menu_keyboard(),
        )

        return

    # =====================================================
    # کد حذف اکانت
    # =====================================================

    if context.user_data.get("waiting_for_code"):

        correct_code = context.user_data.get(
            "delete_code"
        )

        expires = context.user_data.get(
            "delete_expires",
            0,
        )

        # بررسی انقضای کد
        if time.time() > expires:

            context.user_data["waiting_for_code"] = False
            context.user_data["delete_code"] = None
            context.user_data["delete_expires"] = 0

            await update.message.reply_text(
                "⏰ زمان این کد تمام شده است.\n\n"
                "برای حذف اکانت دوباره اقدام کن.",
                reply_markup=main_menu_keyboard(),
            )

            return

        # بررسی کد
        if text == correct_code:

            accounts = load_accounts()

            if user_key in accounts:

                del accounts[user_key]

                save_accounts(accounts)

            context.user_data["waiting_for_code"] = False
            context.user_data["delete_code"] = None
            context.user_data["delete_expires"] = 0

            await update.message.reply_text(
                "✅ اکانتت با موفقیت حذف شد.\n\n"
                "هر وقت خواستی برگردی، "
                "می‌تونی یک اکانت جدید بسازی 🌌",
                reply_markup=main_menu_keyboard(),
            )

        else:

            await update.message.reply_text(
                "❌ کد اشتباه است.\n\n"
                "دوباره کد را وارد کن."
            )

        return

    # =====================================================
    # عملیات پنل سازنده
    # =====================================================

    creator_action = context.user_data.get(
        "creator_action"
    )

    if (
        creator_action
        and is_creator(context)
    ):

        target_id = context.user_data.get(
            "target_user_id"
        )

        accounts = load_accounts()

        if target_id not in accounts:

            context.user_data.pop(
                "creator_action",
                None,
            )

            context.user_data.pop(
                "target_user_id",
                None,
            )

            await update.message.reply_text(
                "❌ اکانت موردنظر پیدا نشد.",
                reply_markup=creator_panel_keyboard(),
            )

            return

        account = accounts[target_id]

        # -------------------------------------------------
        # افزودن سکه
        # -------------------------------------------------

        if creator_action == "add_coins":

            try:
                amount = int(text)

                if amount < 0:
                    raise ValueError

            except ValueError:

                await update.message.reply_text(
                    "❌ مقدار واردشده معتبر نیست.\n\n"
                    "لطفاً فقط یک عدد مثبت وارد کن."
                )

                return

            current_coins = account.get(
                "coins",
                0,
            )

            account["coins"] = (
                current_coins + amount
            )

            save_accounts(accounts)

            context.user_data.pop(
                "creator_action",
                None,
            )

            context.user_data.pop(
                "target_user_id",
                None,
            )

            await update.message.reply_text(
                f"✅ عملیات انجام شد.\n\n"
                f"🪙 مقدار اضافه‌شده: {amount}\n"
                f"🪙 موجودی جدید: {account['coins']}",
                reply_markup=creator_panel_keyboard(),
            )

            return

        # -------------------------------------------------
        # افزودن آیتم
        # -------------------------------------------------

        if creator_action == "add_item":

            items = account.get(
                "items",
                [],
            )

            if not isinstance(items, list):
                items = []

            items.append(text)

            account["items"] = items

            save_accounts(accounts)

            context.user_data.pop(
                "creator_action",
                None,
            )

            context.user_data.pop(
                "target_user_id",
                None,
            )

            await update.message.reply_text(
                f"✅ آیتم با موفقیت اضافه شد.\n\n"
                f"🎒 آیتم: {text}\n"
                f"👤 بازیکن: {account.get('name', 'بی‌نام')}",
                reply_markup=creator_panel_keyboard(),
            )

            return

        # -------------------------------------------------
        # هدیه
        # -------------------------------------------------

        if creator_action == "give_gift":

            gifts = account.get(
                "gifts",
                [],
            )

            if not isinstance(gifts, list):
                gifts = []

            gifts.append(
                {
                    "name": text,
                    "created_at": int(time.time()),
                    "from": "creator",
                }
            )

            account["gifts"] = gifts

            # هدیه را به آیتم‌ها هم اضافه می‌کنیم
            items = account.get(
                "items",
                [],
            )

            if not isinstance(items, list):
                items = []

            items.append(text)

            account["items"] = items

            save_accounts(accounts)

            # اطلاع‌رسانی به بازیکن
            await send_user_message(
                context,
                int(target_id),
                "🎁 یک هدیه از طرف سازنده برایت ارسال شد!\n\n"
                f"🎁 هدیه: {text}\n\n"
                "🌌 از طرف سازنده سلستیا.",
            )

            context.user_data.pop(
                "creator_action",
                None,
            )

            context.user_data.pop(
                "target_user_id",
                None,
            )

            await update.message.reply_text(
                "✅ هدیه با موفقیت برای بازیکن ثبت و ارسال شد.",
                reply_markup=creator_panel_keyboard(),
            )

            return


    # پیام عادی

    accounts = load_accounts()

    if user_key not in accounts:

        await update.message.reply_text(
            "از دکمه‌های زیر استفاده کن 👇",
            reply_markup=main_menu_keyboard(),
        )

        return

    await update.message.reply_text(
        "از دکمه‌های ربات استفاده کن 👇",
        reply_markup=main_menu_keyboard(),
    )


# مدیریت خطا

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    error = context.error

    logger.error(
        "خطای غیرمنتظره:",
        exc_info=error,
    )


# اجرای ربات


def main():

    token = os.environ.get("TOKEN")

    if not token:

        print(
            "❌ خطا: متغیر محیطی TOKEN تنظیم نشده است!"
        )

        return

    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    # دستورات
    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # دکمه‌های شیشه‌ای
    app.add_handler(
        CallbackQueryHandler(
            handle_callback
        )
    )

    # پیام‌های متنی
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    # مدیریت خطا
    app.add_error_handler(
        error_handler
    )

    print(
        "🌌 ربات سلستیا روشن شد..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


# شروع

if __name__ == "__main__":
    main()
