from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

import database
import config
import builder



database.create_database()



users = {}







async def start(update, context):


    keyboard = []


    menus = builder.get_buttons(0)


    for m in menus:


        keyboard.append(
            [
                InlineKeyboardButton(
                    m[1],
                    callback_data=f"menu_{m[0]}"
                )
            ]
        )



    await update.message.reply_text(

        "🌌 به سلستیا خوش آمدی",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )










async def buttons(update, context):


    query = update.callback_query


    await query.answer()



    data = query.data







    # ورود به تنظیمات

    if data == "settings":


        keyboard = [

            [
                InlineKeyboardButton(
                    "👑 اتاق سازنده",
                    callback_data="creator"
                )
            ]

        ]


        await query.edit_message_text(

            "⚙️ تنظیمات",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )









    # شروع ورود سازنده

    elif data == "creator":


        users[query.from_user.id] = "username"


        await query.edit_message_text(

            "نام کاربری سازنده را بفرست:"

        )









    # خانه سازنده

    elif data == "adminhome":


        await admin_home(update,context)









    # اضافه کردن

    elif data == "add":


        users[query.from_user.id] = "new_name"


        await query.edit_message_text(

            "نام دکمه جدید را بفرست:"

        )









    # حذف

    elif data == "delete":



        keyboard=[]


        for m in builder.get_buttons(0):


            if m[1] != "⚙️ تنظیمات":


                keyboard.append(

                    [

                    InlineKeyboardButton(

                        "❌ "+m[1],

                        callback_data=f"del_{m[0]}"

                    )

                    ]

                )



        await query.edit_message_text(

            "کدام حذف شود؟",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )









    # حذف منو

    elif data.startswith("del_"):


        menu_id=int(

            data.replace("del_","")

        )


        builder.delete_button(menu_id)



        await query.edit_message_text(

            "✅ حذف شد"

        )









    # ورود به یک پنل

    elif data.startswith("menu_"):


        menu_id=int(

            data.replace("menu_","")

        )


        await show_panel(

            update,

            context,

            menu_id

        )









    # اضافه کردن زیرمنو

    elif data.startswith("add_"):


        parent=int(

            data.replace("add_","")

        )


        users[query.from_user.id]="child_name"

        users[str(query.from_user.id)+"_parent"]=parent



        await query.edit_message_text(

            "نام زیرمنو را بفرست:"

        )










async def messages(update,context):


    uid=update.message.from_user.id



    if uid not in users:


        await update.message.reply_text(
            "از /start استفاده کن"
        )

        return





    state=users[uid]





    if state=="username":


        users[str(uid)+"_name"]=update.message.text


        users[uid]="password"


        await update.message.reply_text(

            "رمز را بفرست:"

        )







    elif state=="password":


        username=users[str(uid)+"_name"]

        password=update.message.text



        if database.check_login(username,password):


            users[uid]="admin"


            await admin_home(update,context)



        else:


            del users[uid]


            await update.message.reply_text(

                "❌ اشتباه است"

            )








    elif state=="new_name":


        users[str(uid)+"_menu_name"]=update.message.text


        users[uid]="new_text"



        await update.message.reply_text(

            "متن پنل را بفرست:"

        )








    elif state=="new_text":


        name=users[str(uid)+"_menu_name"]


        builder.create_button(

            name,

            update.message.text,

            0

        )


        users[uid]="admin"


        await update.message.reply_text(

            "✅ ساخته شد"

        )








    elif state=="child_name":


        users[str(uid)+"_child_name"]=update.message.text


        users[uid]="child_text"


        await update.message.reply_text(

            "متن پنل را بفرست:"

        )








    elif state=="child_text":


        parent=users[str(uid)+"_parent"]


        builder.create_button(

            users[str(uid)+"_child_name"],

            update.message.text,

            parent

        )


        users[uid]="admin"


        await update.message.reply_text(

            "✅ زیرمنو ساخته شد"

        )











async def admin_home(update,context):


    keyboard=[


        [

        InlineKeyboardButton(
            "➕ اضافه کردن",
            callback_data="add"
        )

        ],


        [

        InlineKeyboardButton(
            "➖ حذف",
            callback_data="delete"
        )

        ]

    ]



    for m in builder.get_buttons(0):


        keyboard.append(

            [

            InlineKeyboardButton(

                m[1],

                callback_data=f"menu_{m[0]}"

            )

            ]

        )



    if update.callback_query:


        await update.callback_query.edit_message_text(

            "🏠 خانه سازنده",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )


    else:


        await update.message.reply_text(

            "🏠 خانه سازنده",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )









async def show_panel(update,context,menu_id):


    query=update.callback_query


    panel=builder.get_panel(menu_id)



    keyboard=[


        [

        InlineKeyboardButton(

            "➕ افزودن",

            callback_data=f"add_{menu_id}"

        )

        ],


        [

        InlineKeyboardButton(

            "⬅️ بازگشت",

            callback_data="adminhome"

        )

        ]

    ]



    for m in builder.get_buttons(menu_id):


        keyboard.append(

            [

            InlineKeyboardButton(

                m[1],

                callback_data=f"menu_{m[0]}"

            )

            ]

        )



    await query.edit_message_text(

        panel[2],

        reply_markup=InlineKeyboardMarkup(keyboard)

    )









app=Application.builder().token(
    config.TOKEN
).build()



app.add_handler(
    CommandHandler(
        "start",
        start
    )
)



app.add_handler(
    CallbackQueryHandler(
        buttons
    )
)



app.add_handler(
    MessageHandler(
        filters.TEXT,
        messages
    )
)



print("Celestia Started...")

app.run_polling()