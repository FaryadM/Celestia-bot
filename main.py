from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

import database
import config
import builder



database.create_database()


users = {}





async def start(update, context):

    keyboard = []


    for m in builder.get_buttons(0):

        keyboard.append(
            [
                InlineKeyboardButton(
                    m[1],
                    callback_data=f"menu_{m[0]}"
                )
            ]
        )


    keyboard.append(
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings"
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

    user_id = query.from_user.id






    if data == "settings":


        keyboard = [

            [
                InlineKeyboardButton(
                    "🔐 ورود به عنوان ادمین",
                    callback_data="admin_login"
                )
            ]

        ]


        await query.edit_message_text(
            "⚙️ تنظیمات",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )






    elif data == "admin_login":


        users[user_id] = "username"


        await query.edit_message_text(
            "نام کاربری ادمین را بفرست:"
        )







    elif data == "admin_home":


        if database.is_admin(user_id):

            await admin_home(update,context)








    elif data == "add":


        if not database.is_admin(user_id):
            return


        users[user_id]="new_name"


        await query.edit_message_text(
            "نام پنل جدید را بفرست:"
        )







    elif data == "delete":


        if not database.is_admin(user_id):
            return


        keyboard=[]


        for m in builder.get_buttons(0):


            if m[1]!="⚙️ تنظیمات":


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







    elif data.startswith("del_"):


        if not database.is_admin(user_id):
            return


        menu_id=int(
            data.replace("del_","")
        )


        builder.delete_button(menu_id)


        await query.edit_message_text(
            "✅ حذف شد"
        )







    elif data.startswith("menu_"):


        menu_id=int(
            data.replace("menu_","")
        )


        await show_panel(
            update,
            context,
            menu_id
        )









async def messages(update,context):


    user_id=update.message.from_user.id


    if user_id not in users:

        await update.message.reply_text(
            "از /start استفاده کن"
        )

        return



    state=users[user_id]





    if state=="username":


        users[str(user_id)+"_name"]=update.message.text


        users[user_id]="password"


        await update.message.reply_text(
            "رمز را بفرست:"
        )






    elif state=="password":


        username=users[str(user_id)+"_name"]

        password=update.message.text



        if database.check_login(username,password):


            database.add_admin_session(user_id)


            users[user_id]="admin"


            await update.message.reply_text(
                "✅ ورود موفق"
            )


            await admin_home(update,context)



        else:


            del users[user_id]


            await update.message.reply_text(
                "❌ اطلاعات اشتباه است"
            )








    elif state=="new_name":


        users[str(user_id)+"_name"]=update.message.text


        users[user_id]="new_text"


        await update.message.reply_text(
            "متن پنل را بفرست:"
        )







    elif state=="new_text":


        builder.create_button(
            users[str(user_id)+"_name"],
            update.message.text,
            0
        )


        users[user_id]="admin"


        await update.message.reply_text(
            "✅ ساخته شد"
        )








async def admin_home(update,context):


    keyboard=[


        [
            InlineKeyboardButton(
                "➕ ساخت پنل",
                callback_data="add"
            )
        ],


        [
            InlineKeyboardButton(
                "➖ حذف پنل",
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
            "👑 خانه ادمین",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    else:


        await update.message.reply_text(
            "👑 خانه ادمین",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )








async def show_panel(update,context,menu_id):


    query=update.callback_query


    panel=builder.get_panel(menu_id)


    keyboard=[]



    if database.is_admin(query.from_user.id):


        keyboard.append(
            [
                InlineKeyboardButton(
                    "➕ افزودن زیرمنو",
                    callback_data=f"add_{menu_id}"
                )
            ]
        )



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