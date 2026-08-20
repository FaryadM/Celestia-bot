import sqlite3


DB = "celestia.db"



def connect():

    return sqlite3.connect(DB)





def create_database():

    con = connect()
    cur = con.cursor()



    # جدول ادمین‌ها

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT

    )
    """)



    # جدول منوها

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menus(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        text TEXT,

        parent INTEGER DEFAULT 0

    )
    """)



    # وضعیت کاربران

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions(

        user_id INTEGER PRIMARY KEY,

        state TEXT

    )
    """)




    # ساخت سازنده اولیه

    cur.execute(
        "SELECT * FROM admins WHERE username=?",
        ("admin",)
    )


    if not cur.fetchone():

        cur.execute(
        """
        INSERT INTO admins(username,password)
        VALUES(?,?)
        """,
        (
            "admin",
            "123456"
        )
        )





    # ساخت تنظیمات اصلی (غیر قابل حذف)

    cur.execute(
        """
        SELECT * FROM menus
        WHERE name=?
        """,
        (
            "⚙️ تنظیمات",
        )
    )


    if not cur.fetchone():

        cur.execute(
        """
        INSERT INTO menus(name,text,parent)
        VALUES(?,?,?)
        """,
        (
            "⚙️ تنظیمات",
            "تنظیمات سلستیا",
            0
        )
        )



    con.commit()
    con.close()






def check_login(username,password):

    con = connect()

    cur = con.cursor()


    cur.execute(
    """
    SELECT * FROM admins
    WHERE username=? AND password=?
    """,
    (
        username,
        password
    )
    )


    result = cur.fetchone()


    con.close()


    return result is not None







def add_menu(name,text,parent=0):

    con = connect()

    cur = con.cursor()



    cur.execute(
    """
    INSERT INTO menus
    (
    name,
    text,
    parent
    )
    VALUES(?,?,?)
    """,
    (
        name,
        text,
        parent
    )
    )


    con.commit()

    con.close()







def get_menus(parent=0):

    con = connect()

    cur = con.cursor()



    cur.execute(
    """
    SELECT id,name,text,parent
    FROM menus
    WHERE parent=?
    """,
    (
        parent,
    )
    )


    result = cur.fetchall()


    con.close()


    return result







def get_menu(menu_id):

    con = connect()

    cur = con.cursor()



    cur.execute(
    """
    SELECT id,name,text,parent
    FROM menus
    WHERE id=?
    """,
    (
        menu_id,
    )
    )


    result = cur.fetchone()


    con.close()


    return result







def delete_menu(menu_id):

    con = connect()

    cur = con.cursor()



    # جلوگیری از حذف تنظیمات

    cur.execute(
    """
    SELECT name FROM menus
    WHERE id=?
    """,
    (
        menu_id,
    )
    )


    item = cur.fetchone()



    if item and item[0] != "⚙️ تنظیمات":


        # حذف زیرمجموعه‌ها

        cur.execute(
        """
        DELETE FROM menus
        WHERE parent=?
        """,
        (
            menu_id,
        )
        )


        # حذف خودش

        cur.execute(
        """
        DELETE FROM menus
        WHERE id=?
        """,
        (
            menu_id,
        )
        )



    con.commit()

    con.close()







def update_text(menu_id,new_text):

    con = connect()

    cur = con.cursor()



    cur.execute(
    """
    UPDATE menus
    SET text=?
    WHERE id=?
    """,
    (
        new_text,
        menu_id
    )
    )


    con.commit()

    con.close()