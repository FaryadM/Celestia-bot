import os
import sqlite3
import asyncio
import time
import hashlib

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# ==========================
# تنظیمات اصلی
# ==========================

ADMIN_USERNAME = "creator"
ADMIN_PASSWORD = "123456"

FORCE_CHANNEL = "@YourChannel"


# ==========================
# دیتابیس
# ==========================

db = sqlite3.connect(
    "celestia.db",
    check_same_thread=False
)

cursor = db.cursor()


def create_database():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        gold INTEGER DEFAULT 100,
        level INTEGER DEFAULT 1,
        hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        attack INTEGER DEFAULT 10,
        defense INTEGER DEFAULT 5,
        character_name TEXT,
        permanent INTEGER DEFAULT 0,
        login_username TEXT,
        login_password TEXT,
        last_rest INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS texts(
        name TEXT PRIMARY KEY,
        value TEXT
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY
    )
    """)


    db.commit()



create_database()



# ==========================
# ابزارها
# ==========================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()



def get_user(user_id):

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    return cursor.fetchone()



def create_user(user_id, username):

    cursor.execute("""
    INSERT INTO users(
    user_id,
    username
    )
    VALUES(?,?)
    """,
    (
        user_id,
        username
    ))

    db.commit()



def save():

    db.commit()



# ==========================
# عضویت کانال
# ==========================


async def check_member(update, context):

    user_id = update.effective_user.id

    try:

        member = await context.bot.get_chat_member(
            FORCE_CHANNEL,
            user_id
        )

        if member.status in [
            "member",
            "administrator",
            "creator"
        ]:
            return True


    except:
        pass


    keyboard = [
        [
            InlineKeyboardButton(
                "عضویت در کانال",
                url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"
            )
        ],
        [
            InlineKeyboardButton(
                "بررسی عضویت",
                callback_data="check_join"
            )
        ]
    ]


    await update.message.reply_text(
        "برای ورود به دنیای سلستیا ابتدا در کانال عضو شوید ⚔️",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


    return False



# ==========================
# استارت
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await check_member(update, context):
        return


    user = update.effective_user

    data = get_user(user.id)


    if not data:

        create_user(
            user.id,
            user.username or ""
        )


    text = """
🌌 به دنیای سلستیا خوش آمدید

سرزمینی پر از شمشیر، جادو و افسانه...

در این دنیا شما قهرمان خودتان هستید.
ماجراجویی کنید، دشمنان را شکست دهید،
آیتم جمع کنید و قدرت بگیرید ⚔️

آماده‌ای قهرمان سلستیا شوی؟
"""


    keyboard = [

        [
            InlineKeyboardButton(
                "👤 پروفایل",
                callback_data="profile"
            ),

            InlineKeyboardButton(
                "⚔️ ماجراجویی",
                callback_data="adventure"
            )
        ],

        [
            InlineKeyboardButton(
                "🎒 آیتم‌ها",
                callback_data="items"
            ),

            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings"
            )
        ]

    ]


    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# ==========================
# دکمه ها
# ==========================


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()


    user_id = query.from_user.id


    if query.data=="check_join":

        await start(update,context)
        return



    if query.data=="settings":

        keyboard=[

        [
        InlineKeyboardButton(
        "💾 ساخت اکانت دائمی",
        callback_data="make_account"
        )
        ],

        [
        InlineKeyboardButton(
        "🗑 حذف اکانت",
        callback_data="delete_account"
        )
        ],

        [
        InlineKeyboardButton(
        "🔐 ورود مدیریت",
        callback_data="admin_login"
        )
        ]

        ]


        await query.edit_message_text(
            "⚙️ تنظیمات سلستیا",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )



    elif query.data=="profile":

        user=get_user(user_id)

        text=f"""
👤 پروفایل قهرمان

❤️ سلامتی: {user[4]}/{user[5]}
⚔️ قدرت: {user[6]}
🛡 دفاع: {user[7]}
💰 طلا: {user[2]}
⭐ سطح: {user[3]}
"""

        await query.edit_message_text(text)


# ==========================
# ساخت اکانت دائمی
# ==========================


async def make_account_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["creating_account"] = True

    await query.edit_message_text(
        """
💾 ساخت اکانت دائمی

لطفاً یک نام کاربری برای اکانت خود ارسال کنید:

مثال:
AriaKnight
"""
    )



async def receive_account_username(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("creating_account"):
        return


    context.user_data["account_username"] = update.message.text

    await update.message.reply_text(
        """
🔐 حالا رمز عبور اکانت را ارسال کنید:
"""
    )


    context.user_data["waiting_password"] = True



async def receive_account_password(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_password"):
        return


    password = hash_password(
        update.message.text
    )


    username = context.user_data.get(
        "account_username"
    )


    user_id = update.effective_user.id


    cursor.execute("""
    UPDATE users SET

    permanent=1,
    login_username=?,
    login_password=?

    WHERE user_id=?

    """,
    (
        username,
        password,
        user_id
    ))


    db.commit()


    context.user_data.clear()


    await update.message.reply_text(
        """
✅ اکانت شما دائمی شد

از این پس حتی با ریست شدن ربات،
اطلاعات شخصیت شما حفظ خواهد شد ⚔️
"""
    )





# ==========================
# حذف اکانت
# ==========================


async def delete_account_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query

    await query.answer()


    keyboard=[

        [
        InlineKeyboardButton(
            "🗑 حذف اکانت فعلی",
            callback_data="delete_current"
        )
        ],

        [
        InlineKeyboardButton(
            "🔥 حذف اکانت دائمی",
            callback_data="delete_permanent"
        )
        ]

    ]


    await query.edit_message_text(
        """
انتخاب کنید:

⚠️ حذف اکانت باعث از بین رفتن اطلاعات می‌شود
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )




async def delete_confirm(update,context):

    query=update.callback_query

    await query.answer()


    context.user_data["delete_wait"]=True


    await query.edit_message_text(
        """
آیا مطمئن هستید؟

برای حذف بنویسید:
تایید

برای لغو:
لغو
"""
    )




async def delete_account_confirm(update,context):

    if not context.user_data.get("delete_wait"):
        return


    user_id=update.effective_user.id


    if update.message.text=="تایید":

        cursor.execute(
        """
        DELETE FROM users
        WHERE user_id=?
        """,
        (user_id,)
        )


        db.commit()


        await update.message.reply_text(
            """
🗑 اکانت شما حذف شد

برای شروع دوباره /start را بزنید
"""
        )


    else:

        await update.message.reply_text(
            "❌ حذف لغو شد"
        )


    context.user_data.clear()




async def delete_permanent(update,context):

    query=update.callback_query

    await query.answer()


    user_id=query.from_user.id


    cursor.execute("""
    UPDATE users SET

    permanent=0,
    login_username=NULL,
    login_password=NULL

    WHERE user_id=?

    """,
    (user_id,)
    )


    db.commit()


    await query.edit_message_text(
        """
🔥 اکانت دائمی حذف شد

اطلاعات فعلی بازی شما باقی می‌ماند.
"""
    )





# ==========================
# ماجراجویی
# ==========================


async def adventure(update,context):

    query=update.callback_query

    await query.answer()


    keyboard=[

    [
    InlineKeyboardButton(
        "👹 حمله به هیولا",
        callback_data="battle"
    )
    ]

    ]


    await query.edit_message_text(
        """
🌲 جنگل سلستیا

صدای قدم‌های یک موجود ناشناس می‌آید...

آیا وارد نبرد می‌شوید؟
""",

reply_markup=InlineKeyboardMarkup(keyboard)

    )





# ==========================
# سیستم جنگ ساده
# ==========================


monsters=[

    {
        "name":"گرگ تاریکی",
        "hp":50,
        "attack":8
    },

    {
        "name":"جادوگر سایه",
        "hp":80,
        "attack":12
    }

]



async def battle_start(update,context):

    query=update.callback_query

    await query.answer()


    monster=monsters[
        int(time.time()) % len(monsters)
    ]


    context.user_data["monster"]=monster.copy()


    keyboard=[

    [
    InlineKeyboardButton(
        "⚔️ حمله",
        callback_data="attack"
    ),

    InlineKeyboardButton(
        "🛡 دفاع",
        callback_data="defend"
    )
    ]

    ]


    await query.edit_message_text(

f"""
👹 دشمن ظاهر شد

{monster['name']}

❤️ جان دشمن:
{monster['hp']}

حرکت خود را انتخاب کنید:
""",

reply_markup=InlineKeyboardMarkup(keyboard)

    )





async def battle_move(update,context):

    query=update.callback_query

    await query.answer()


    user_id=query.from_user.id


    user=get_user(user_id)


    monster=context.user_data.get(
        "monster"
    )


    if not monster:
        return



    if query.data=="attack":

        monster["hp"]-=user[6]


        if monster["hp"]<=0:


            cursor.execute(
            """
            UPDATE users SET
            gold=gold+50,
            level=level+1
            WHERE user_id=?
            """,
            (user_id,)
            )

            db.commit()


            await query.edit_message_text(
            """
🏆 پیروز شدید!

+50 طلا
+1 سطح
"""
            )

            return



        damage=monster["attack"]


        cursor.execute(
        """
        UPDATE users SET hp=hp-?
        WHERE user_id=?
        """,
        (
        damage,
        user_id
        )
        )


        db.commit()


        await query.edit_message_text(
f"""
⚔️ ضربه زدید

جان دشمن:
{monster['hp']}

دشمن به شما {damage} آسیب زد
"""
        )



    elif query.data=="defend":


        await query.edit_message_text(
        """
🛡 حالت دفاعی فعال شد

اگر شکست بخورید باید ۱ دقیقه استراحت کنید.
"""
        )
        
        # ==========================
# پنل مدیریت سازنده
# ==========================


async def admin_login_start(update, context):

    query = update.callback_query

    await query.answer()


    context.user_data["admin_login"] = True
    context.user_data["admin_step"] = "username"


    await query.edit_message_text(
        """
🔐 ورود به بخش مدیریت

نام کاربری سازنده را ارسال کنید:
"""
    )





async def admin_login_receive(update, context):

    if not context.user_data.get("admin_login"):
        return


    step = context.user_data.get(
        "admin_step"
    )


    if step=="username":

        context.user_data["admin_username_input"] = update.message.text

        context.user_data["admin_step"]="password"


        await update.message.reply_text(
            "🔑 رمز مدیریت را ارسال کنید:"
        )



    elif step=="password":

        username=context.user_data.get(
            "admin_username_input"
        )


        password=update.message.text


        if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:


            cursor.execute(
            """
            INSERT OR IGNORE INTO admins(user_id)
            VALUES(?)
            """,
            (
            update.effective_user.id,
            )
            )


            db.commit()


            context.user_data.clear()


            await update.message.reply_text(
                """
👑 وارد پنل مدیریت شدید

دسترسی کامل فعال شد.
"""
                ,
                reply_markup=admin_keyboard()
            )


        else:

            context.user_data.clear()

            await update.message.reply_text(
                "❌ اطلاعات اشتباه است"
            )





def admin_keyboard():

    keyboard=[

    [
    InlineKeyboardButton(
        "➕ ساخت دکمه",
        callback_data="admin_button_create"
    )
    ],

    [
    InlineKeyboardButton(
        "📦 ساخت آیتم",
        callback_data="admin_item_create"
    )
    ],

    [
    InlineKeyboardButton(
        "💰 تغییر قیمت",
        callback_data="admin_price"
    )
    ],

    [
    InlineKeyboardButton(
        "📢 پیام به کاربران",
        callback_data="admin_broadcast"
    )
    ],

    [
    InlineKeyboardButton(
        "🚫 مدیریت کاربران",
        callback_data="admin_users"
    )
    ],

    [
    InlineKeyboardButton(
        "📖 مدیریت داستان",
        callback_data="admin_story"
    )
    ]

    ]


    return InlineKeyboardMarkup(keyboard)







# ==========================
# بررسی ادمین
# ==========================


def is_admin(user_id):

    cursor.execute(
        """
        SELECT * FROM admins
        WHERE user_id=?
        """,
        (user_id,)
    )


    return cursor.fetchone() is not None






# ==========================
# ساخت دکمه جدید توسط سازنده
# ==========================


async def admin_create_button(update,context):


    query=update.callback_query

    await query.answer()


    if not is_admin(query.from_user.id):

        return



    context.user_data["admin_action"]="button_name"


    await query.edit_message_text(
        """
➕ ساخت دکمه جدید

نام دکمه را ارسال کنید:
"""
    )







async def admin_create_button_receive(update,context):


    action=context.user_data.get(
        "admin_action"
    )


    if action=="button_name":


        context.user_data["new_button_name"]=update.message.text

        context.user_data["admin_action"]="button_text"


        await update.message.reply_text(
            """
متنی که بعد از زدن دکمه نمایش داده شود را ارسال کنید:
"""
        )



    elif action=="button_text":


        name=context.user_data.get(
            "new_button_name"
        )


        text=update.message.text


        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_buttons(
        
        name TEXT PRIMARY KEY,
        text TEXT
        
        )
        """
        )


        cursor.execute(
        """
        INSERT OR REPLACE INTO custom_buttons
        VALUES(?,?)
        """,
        (
        name,
        text
        )
        )


        db.commit()


        context.user_data.clear()


        await update.message.reply_text(
            """
✅ دکمه جدید ساخته شد
"""
        )






# ==========================
# ساخت آیتم
# ==========================


async def admin_item_create(update,context):


    query=update.callback_query

    await query.answer()


    context.user_data["admin_action"]="item"


    await query.edit_message_text(
        """
📦 ساخت آیتم

اطلاعات آیتم را اینگونه بفرست:

نام آیتم | قیمت | قدرت
"""
    )






async def admin_item_receive(update,context):


    if context.user_data.get(
        "admin_action"
    )!="item":

        return


    try:

        name,price,power=update.message.text.split("|")


        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS items(

        name TEXT,
        price INTEGER,
        power INTEGER

        )
        """
        )


        cursor.execute(
        """
        INSERT INTO items VALUES(?,?,?)
        """,
        (
        name,
        int(price),
        int(power)
        )
        )


        db.commit()



        context.user_data.clear()


        await update.message.reply_text(
            """
✅ آیتم ساخته شد
"""
        )


    except:


        await update.message.reply_text(
            """
فرمت اشتباه است

مثال:

شمشیر آتش | 500 | 20
"""
        )






# ==========================
# پیام همگانی
# ==========================


async def admin_broadcast(update,context):


    query=update.callback_query

    await query.answer()


    context.user_data["admin_action"]="broadcast"


    await query.edit_message_text(
        """
📢 متن پیام همگانی را ارسال کنید:
"""
    )





async def broadcast_receive(update,context):


    if context.user_data.get(
        "admin_action"
    )!="broadcast":

        return



    text=update.message.text


    cursor.execute(
        "SELECT user_id FROM users"
    )


    users=cursor.fetchall()



    count=0


    for user in users:

        try:

            await context.bot.send_message(
                user[0],
                text
            )

            count+=1


        except:

            pass



    context.user_data.clear()



    await update.message.reply_text(
f"""
✅ پیام ارسال شد

تعداد:
{count}
"""
    )

# ==========================
# مدیریت داستان
# ==========================


async def admin_story(update, context):

    query = update.callback_query
    await query.answer()


    if not is_admin(query.from_user.id):
        return


    context.user_data["admin_action"] = "story"


    await query.edit_message_text(
        """
📖 مدیریت داستان

نام بخش و متن جدید را ارسال کنید:

فرمت:

نام بخش | متن داستان

مثال:

forest | وارد جنگل تاریک شدید...
"""
    )





async def story_receive(update, context):

    if context.user_data.get(
        "admin_action"
    ) != "story":

        return


    try:

        name, text = update.message.text.split("|",1)


        cursor.execute(
        """
        INSERT OR REPLACE INTO texts
        VALUES(?,?)
        """,
        (
        name.strip(),
        text.strip()
        )
        )


        db.commit()


        context.user_data.clear()


        await update.message.reply_text(
            """
✅ داستان ذخیره شد
"""
        )


    except:


        await update.message.reply_text(
            """
فرمت اشتباه است
"""
        )





# ==========================
# دکمه های سفارشی
# ==========================


async def show_custom_buttons(update, context):

    query = update.callback_query

    await query.answer()


    cursor.execute(
    """
    SELECT name FROM custom_buttons
    """
    )


    buttons=[]


    for row in cursor.fetchall():

        buttons.append(
        [
        InlineKeyboardButton(
            row[0],
            callback_data=f"custom_{row[0]}"
        )
        ]
        )



    if buttons:

        await query.edit_message_text(
            "منوی ویژه:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )



async def custom_button_click(update,context):

    query=update.callback_query

    await query.answer()


    name=query.data.replace(
        "custom_",
        ""
    )


    cursor.execute(
    """
    SELECT text FROM custom_buttons
    WHERE name=?
    """,
    (name,)
    )


    data=cursor.fetchone()


    if data:


        await query.edit_message_text(
            data[0]
        )





# ==========================
# حذف و مدیریت کاربران
# ==========================


async def admin_users(update,context):


    query=update.callback_query

    await query.answer()


    if not is_admin(query.from_user.id):

        return


    context.user_data["admin_action"]="users"


    await query.edit_message_text(
        """
🚫 مدیریت کاربران

برای حذف کاربر:

delete USER_ID

برای بن کردن:

ban USER_ID
"""
    )






async def admin_users_receive(update,context):


    if context.user_data.get(
        "admin_action"
    )!="users":

        return


    try:

        command,user_id=update.message.text.split()


        user_id=int(user_id)


        if command=="delete":


            cursor.execute(
            """
            DELETE FROM users
            WHERE user_id=?
            """,
            (user_id,)
            )



        elif command=="ban":


            cursor.execute(
            """
            UPDATE users
            SET banned=1
            WHERE user_id=?
            """,
            (user_id,)
            )



        db.commit()


        await update.message.reply_text(
            "✅ انجام شد"
        )


    except:


        await update.message.reply_text(
            "فرمت اشتباه"
        )





# ==========================
# بررسی بن بودن
# ==========================


async def check_ban(update,context):


    user=get_user(
        update.effective_user.id
    )


    if user and user[13]==1:

        await update.message.reply_text(
            "🚫 شما از بازی اخراج شده‌اید"
        )

        return True


    return False





# ==========================
# اتصال هندلرها
# ==========================


def main():


    app = Application.builder().token(
        BOT_TOKEN
    ).build()



    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            make_account_start,
            pattern="make_account"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            delete_account_menu,
            pattern="delete_account"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            delete_confirm,
            pattern="delete_current"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            delete_permanent,
            pattern="delete_permanent"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            adventure,
            pattern="adventure"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            battle_start,
            pattern="battle"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            battle_move,
            pattern="attack|defend"
        )
    )



    app.add_handler(
        CallbackQueryHandler(
            admin_login_start,
            pattern="admin_login"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            admin_create_button,
            pattern="admin_button_create"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            admin_item_create,
            pattern="admin_item_create"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            admin_broadcast,
            pattern="admin_broadcast"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            admin_story,
            pattern="admin_story"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            admin_users,
            pattern="admin_users"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )



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


    # پیام های متنی

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_account_username
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_account_password
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_login_receive
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_create_button_receive
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_item_receive
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            broadcast_receive
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            story_receive
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_users_receive
        )
    )


    print(
        "Celestia Started..."
    )


    app.run_polling()





if __name__=="__main__":

    main()
