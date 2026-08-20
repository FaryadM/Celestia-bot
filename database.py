import sqlite3


DB = "celestia.db"



def connect():

    return sqlite3.connect(DB)





def create_database():

    con = connect()

    cur = con.cursor()



    # کاربران ادمین

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT

    )
    """)



    # منوها

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menus(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        text TEXT,

        parent INTEGER DEFAULT 0

    )
    """)



    # وضعیت ورود کاربران

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions(

        user_id INTEGER PRIMARY KEY

    )
    """)




    # ساخت ادمین اولیه

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





    # ساخت تنظیمات اصلی

    cur.execute(
        """
        SELECT * FROM menus
        WHERE name=?
        """,
        ("⚙️ تنظیمات",)
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

    con=connect()

    cur=con.cursor()



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


    result=cur.fetchone()


    con.close()


    return result is not None







def add_admin_session(user_id):

    con=connect()

    cur=con.cursor()



    cur.execute(
        """
        INSERT OR IGNORE INTO admin_sessions(user_id)
        VALUES(?)
        """,
        (
            user_id,
        )
    )


    con.commit()

    con.close()







def remove_admin_session(user_id):

    con=connect()

    cur=con.cursor()



    cur.execute(
        """
        DELETE FROM admin_sessions
        WHERE user_id=?
        """,
        (
            user_id,
        )
    )


    con.commit()

    con.close()







def is_admin(user_id):

    con=connect()

    cur=con.cursor()



    cur.execute(
        """
        SELECT * FROM admin_sessions
        WHERE user_id=?
        """,
        (
            user_id,
        )
    )


    result=cur.fetchone()


    con.close()


    return result is not None







def add_menu(name,text,parent=0):

    con=connect()

    cur=con.cursor()



    cur.execute(
        """
        INSERT INTO menus(name,text,parent)
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

    con=connect()

    cur=con.cursor()



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


    data=cur.fetchall()


    con.close()


    return data







def get_menu(menu_id):

    con=connect()

    cur=con.cursor()



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


    data=cur.fetchone()


    con.close()


    return data







def delete_menu(menu_id):

    con=connect()

    cur=con.cursor()



    cur.execute(
        """
        SELECT name FROM menus
        WHERE id=?
        """,
        (
            menu_id,
        )
    )


    item=cur.fetchone()



    if item and item[0]!="⚙️ تنظیمات":


        cur.execute(
            """
            DELETE FROM menus
            WHERE parent=?
            """,
            (
                menu_id,
            )
        )


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