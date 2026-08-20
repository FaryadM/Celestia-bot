import database






def create_button(name, text, parent=0):

    database.add_menu(
        name,
        text,
        parent
    )







def get_buttons(parent=0):

    menus = database.get_menus(parent)


    result = []


    for menu in menus:

        # تنظیمات را در حذف و ساخت منو جدا نگه می‌داریم

        result.append(menu)


    return result







def get_panel(menu_id):

    return database.get_menu(menu_id)







def delete_button(menu_id):

    database.delete_menu(menu_id)







def update_panel_text(menu_id,text):

    database.update_text(
        menu_id,
        text
    )