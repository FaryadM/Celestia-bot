import json
import os
import random
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)


#  ⚙️ تنظیمات اصلی

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@Celestia_world1"   # کانال اجباری
CREATOR_ID = 8433719957                  # آیدی عددی ادمین اصلی (خودت عوض کن)
DATA_FILE = "players.json"
ADMIN_FILE = "admins.json"
ITEMS_FILE = "items.json"
MONSTERS_FILE = "monsters.json"
MATERIALS_FILE = "materials.json"
GUILDS_FILE = "guilds.json"
PARTIES_FILE = "parties.json"
FROZEN_FILE = "frozen.json"


#  💾 توابع ذخیره و بارگذاری

def load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_players():    return load_json(DATA_FILE, {})
def save_players(d):   save_json(DATA_FILE, d)
def load_items():      return load_json(ITEMS_FILE, {})
def save_items(d):     save_json(ITEMS_FILE, d)
def load_monsters():   return load_json(MONSTERS_FILE, {})
def save_monsters(d):  save_json(MONSTERS_FILE, d)
def load_materials():  return load_json(MATERIALS_FILE, {})
def save_materials(d): save_json(MATERIALS_FILE, d)
def load_guilds():     return load_json(GUILDS_FILE, {})
def save_guilds(d):    save_json(GUILDS_FILE, d)
def load_parties():    return load_json(PARTIES_FILE, {})
def save_parties(d):   save_json(PARTIES_FILE, d)
def load_frozen():     return load_json(FROZEN_FILE, {"frozen": False})
def save_frozen(d):    save_json(FROZEN_FILE, d)
def load_admins():     return load_json(ADMIN_FILE, {"admins": [CREATOR_ID]})
def save_admins(d):    save_json(ADMIN_FILE, d)

def get_player(user_id, first_name):
    players = load_players()
    uid = str(user_id)
    if uid not in players:
        players[uid] = {
            "telegram_id": user_id,
            "username_login": None,
            "password": None,
            "name": first_name,
            "gender": None,
            "race": None,
            "level": 1,
            "xp": 0,
            "xp_needed": 100,
            "hp": 100, "max_hp": 100,
            "attack": 10, "defense": 10,
            "speed": 10, "mana": 1,
            "crit_dmg": 1.0, "crit_hit": 0,
            "class": "بدون کلاس",
            "coins": 1000,
            "bank_coins": 0,
            "bank_time": 0,
            "inventory": [],
            "equipped": {"weapon": None, "armor": None, "ring": None, "boots": None, "necklace": None},
            "skills": ["تازه‌کار"],
            "wins": 0, "losses": 0,
            "guild": None,
            "party": None,
            "friends": [],
            "online": False,
            "banned": False,
            "level_blocked": False,
            "created_at": int(time.time()),
        }
        save_players(players)
    return players[uid]

def update_player(user_id, data):
    players = load_players()
    players[str(user_id)] = data
    save_players(players)

# =====================================================
#  🛠 توابع کمکی
# =====================================================
def is_creator(user_id):
    return user_id == CREATOR_ID

def is_admin(user_id):
    admins = load_admins()
    return user_id in admins.get("admins", [])

def is_frozen():
    return load_frozen().get("frozen", False)

def make_hp_bar(cur, mx, length=10):
    filled = int((cur / mx) * length) if mx > 0 else 0
    return f"[{'█' * filled}{'░' * (length - filled)}] {cur}/{mx}"

def add_xp(player, amount):
    if player.get("level_blocked"):
        return False
    player["xp"] += amount
    leveled = False
    while player["xp"] >= player["xp_needed"]:
        player["xp"] -= player["xp_needed"]
        player["level"] += 1
        player["max_hp"] += 20
        player["hp"] = player["max_hp"]
        player["attack"] += 5
        player["defense"] += 5
        player["speed"] += 2
        player["mana"] += 1
        player["xp_needed"] = int(player["xp_needed"] * 1.5)
        leveled = True
    return leveled

def back_keyboard(target="home"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=target)]])

def close_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ بستن", callback_data="close")]])

def back_and_close(target="home"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=target),
         InlineKeyboardButton("❌ بستن", callback_data="close")]
    ])

# =====================================================
#  📜 منوهای اصلی
# =====================================================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile")],
        [InlineKeyboardButton("🏰 شهر", callback_data="city"),
         InlineKeyboardButton("⚔️ میدان نبرد", callback_data="battle_field")],
        [InlineKeyboardButton("🎒 کوله‌بار", callback_data="inventory"),
         InlineKeyboardButton("🏛 انجمن", callback_data="guild_menu")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
    ])

def settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 ساخت اکانت دائمی", callback_data="create_permanent")],
        [InlineKeyboardButton("🗼 برج خدایان", callback_data="god_tower")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home")],
    ])

 
#  👋 دستور /start — چک عضویت کانال
# =====================================================
async def check_channel_membership(update, context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # چک اکانت بن شده
    player = get_player(user.id, user.first_name or "بازیکن")
    if player.get("banned"):
        await update.message.reply_text("⛔️ شما از ربات تبعید شدید.")
        return

    # چک فریز بودن ربات
    if is_frozen() and not is_admin(user.id):
        await update.message.reply_text("❄️ ربات در حالت انجماد است. فقط ادمین‌ها دسترسی دارند.")
        return

    # چک عضویت کانال
    is_member = await check_channel_membership(update, context, user.id)
    if not is_member:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")],
        ])
        await update.message.reply_text(
            "شما در کانال رسمی عضو نیستی\n\n"
            "لطفاً برای ورود به سلستیا ابتدا عضو کانال شوید:",
            reply_markup=keyboard,
        )
        return

    # اگه اکانت ساخته نشده
    if player["race"] is None:
        await update.message.reply_text(
            "✅ عضویت تایید شد!\n\n"
            "برای شروع ثبت‌نام و ساخت کاراکتر، لطفاً روی دستور /start کلیک کن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✨ ساخت کاراکتر", callback_data="create_char")]
            ]),
        )
        return

    # منوی اصلی
    await show_profile(update, context, player)

async def show_profile(update, context, player):
    text = format_profile(player)
    keyboard = main_menu_keyboard()
    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

def format_profile(p):
    gender_text = "👨 مرد" if p["gender"] == "male" else "👩 زن" if p["gender"] == "female" else "—"
    race_emoji = {"human": "🧑🏻", "elf": "🧝", "dwarf": "⛏️", "majin": "🔮", "orc": "👹", "demon": "🧛🏼", "angel": "👼🏻"}.get(p["race"], "—")
    race_name = {"human": "انسان", "elf": "الف", "dwarf": "دورف", "majin": "ماجین", "orc": "اورک", "demon": "اهریمن", "angel": "فرشته"}.get(p["race"], "—")
    return (
        f"👤 **{p['name']}**\n"
        f"🆔 آیدی: `{p['telegram_id']}` | 🏆 رتبه جهانی #?\n"
        f"🫆 نژاد: {race_emoji} {race_name} | جنسیت: {gender_text}\n"
        f"🌀 سبک نبرد: {p.get('class', 'بدون کلاس')}\n"
        f"━━━━━━━━━━━━━\n"
        f"📊 سطح {p['level']} {make_hp_bar(p['level'], 100, 10)}\n\n"
        f"⚔️ حمله {p['attack']} | 🛡 دفاع {p['defense']}\n"
        f"⚡️ سرعت {p['speed']} | 🔮 مانا {p['mana']}\n"
        f"💥 Crit DMG ×{p['crit_dmg']} | 🎲 Crit Hit: {p['crit_hit']}%\n"
        f"━━━━━━━━━━━━━\n"
        f"🪙 سکه: {p['coins']}\n"
        f"📖 مهارت‌ها: {', '.join(p['skills'])}\n"
        f"🏛 انجمن: {p.get('guild') or '—'}\n\n"
        f"🌍 **شهر سلستیا** [🟢 سطح آسان]"
    )

# =====================================================
#  🎭 ساخت کاراکتر
# =====================================================
async def create_char(query, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨 مرد", callback_data="gender_male"),
         InlineKeyboardButton("👩 زن", callback_data="gender_female")],
    ])
    await query.edit_message_text("نام ماجراجو:", reply_markup=keyboard)

async def ask_name(update, context):
    context.user_data["awaiting_name"] = True
    await update.message.reply_text("🎭 یه اسم برای کاراکترت انتخاب کن:")

RACES = {
    "human": ("🧑🏻 انسان", "❇️ امکان یادگیری همه چیز\n⛔️ فاقد مهارت خاص در شروع بازی"),
    "elf": ("🧝 الف", "❇️ مهارت کمانداری و جادو بالا\n⛔️ ضعف در یادگیری مهارت‌های دیگر"),
    "dwarf": ("⛏️ دورف", "❇️ مهارت آهنگری و صنعتگری\n⛔️ ضعف در استفاده از جادو"),
    "majin": ("🔮 ماجین", "❇️ مهارت خوش‌شانسی (دراپ آیتم بیشتر)\n⛔️ ضعف در یادگیری طلسم‌های جادویی"),
    "orc": ("👹 اورک", "❇️ مهارت خشم (افزایش قدرت در نبرد)\n✳️ مصونیت در برابر جادو\n⛔️ ضعف در استفاده از جادو"),
    "demon": ("🧛🏼 اهریمن", "❇️ مهارت جادوی تاریک و نفرین‌ها\n⛔️ ضعف در برابر جادو و طلسم نور"),
    "angel": ("👼🏻 فرشته", "❇️ مهارت جادوی نور و درمان\n⛔️ ضعف در برابر طلسم تاریکی\n⛔️ ضعف در قدرت فیزیکی"),
}

def reincarnation_keyboard():
    rows = [
        [InlineKeyboardButton("⬜", callback_data="dummy")],
        [InlineKeyboardButton("⬜", callback_data="dummy"), InlineKeyboardButton("⬜", callback_data="dummy")],
        [InlineKeyboardButton("⬜", callback_data="dummy"), InlineKeyboardButton("⬜", callback_data="dummy")],
        [InlineKeyboardButton("⬜", callback_data="dummy"), InlineKeyboardButton("⬜", callback_data="dummy")],
    ]
    races_list = list(RACES.keys())
    mapping = {
        0: "human", 1: "elf", 2: "dwarf",
        3: "majin", 4: "orc", 5: "demon", 6: "angel",
    }
    labels = [
        ("🧑🏻 انسان", "human"), ("🧝 الف", "elf"),
        ("⛏️ دورف", "dwarf"), ("🔮 ماجین", "majin"),
        ("👹 اورک", "orc"), ("🧛🏼 اهریمن", "demon"),
        ("👼🏻 فرشته", "angel"),
    ]
    btn_grid = [
        [InlineKeyboardButton(labels[0][0], callback_data=f"race_{labels[0][1]}")],
        [InlineKeyboardButton(labels[1][0], callback_data=f"race_{labels[1][1]}"),
         InlineKeyboardButton(labels[2][0], callback_data=f"race_{labels[2][1]}")],
        [InlineKeyboardButton(labels[3][0], callback_data=f"race_{labels[3][1]}"),
         InlineKeyboardButton(labels[4][0], callback_data=f"race_{labels[4][1]}")],
        [InlineKeyboardButton(labels[5][0], callback_data=f"race_{labels[5][1]}"),
         InlineKeyboardButton(labels[6][0], callback_data=f"race_{labels[6][1]}")],
    ]
    return InlineKeyboardMarkup(btn_grid)

async def show_reincarnation(query):
    await query.edit_message_text(
        "به دنیای سلستیا خوش اومدی!\nدنیای شمشیر و جادو در انتظار توئه…\n\n"
        "یک مسیر تناسخ رو انتخاب کنید:",
        reply_markup=reincarnation_keyboard(),
    )

async def show_race_info(query, race_key):
    name, desc = RACES[race_key]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ادامه ➡️", callback_data=f"confirm_race_{race_key}"),
         InlineKeyboardButton("🔙 بازگشت", callback_data="back_reincarnation")]
    ])
    text = f"{name}\n\n{desc}"
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def confirm_race(query, context, player, race_key):
    name, _ = RACES[race_key]
    player["race"] = race_key
    update_player(player["telegram_id"], player)
    story = (
        "پس از تناسخ، چشمانت را در نزدیکی شهر بزرگ سلستیا باز می‌کنی.\n"
        "شهری آرام که محل رفت‌وآمد تاجران و ماجراجویان است.\n"
        "مسیر تو با تلاش و انتخاب‌هایت ساخته خواهد شد.\n\n"
        "برای شروع می‌توانی وارد مسافرخانه «ماه نقره‌ای» شوی و استراحت کنی.\n\n"
        "در بازار سلستیا و مزایده‌های انجمن می‌تونی آیتم‌های مورد نیاز رو تهیه کنی.\n\n"
        "در گوشه‌وکنار شهر، مأموریت‌های ساده‌ای برای کسب تجربه و پول وجود داره ولی "
        "برای مأموریت‌های سخت‌تر و دریافت پاداش‌های بیشتر، به انجمن ماجراجویان (Guild) ملحق شو.\n\n"
        "هر تصمیمی که بگیری، مسیر زندگی جدیدت را در این دنیا تغییر خواهد داد.\n\n"
        "ماجراجوییت در سلستیا از همین لحظه آغاز می‌شه..."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ شروع ماجراجویی", callback_data="home")],
    ])
    await query.edit_message_text(story, reply_markup=keyboard)


# =====================================================
#  🏰 شهر
# =====================================================
def city_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏡 مسافرخانه", callback_data="inn"),
         InlineKeyboardButton("🏪 بازار", callback_data="market")],
        [InlineKeyboardButton("⛪️ کلیسا", callback_data="church"),
         InlineKeyboardButton("⚒ آهنگری", callback_data="blacksmith")],
        [InlineKeyboardButton("🏦 خزانه", callback_data="bank")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_city(query):
    await query.edit_message_text("🏰 **شهر سلستیا**\n\nکجا میخوای بری؟", reply_markup=city_keyboard(), parse_mode="Markdown")

async def show_inn(query, player):
    text = (
        "🍺 **مسافرخانه ماه نقره‌ای**\n\n"
        "میخوای از جیب ریشو ۱۰ سکه بدی و استراحت کنی؟\n"
        "استراحت = پر شدن HP و انرژی."
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💤 استراحت (10 سکه)", callback_data="rest")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="city"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

async def do_rest(query, player):
    if player["coins"] < 10:
        await query.answer("❌ سکه کافی نداری!", show_alert=True)
        return
    player["coins"] -= 10
    player["hp"] = player["max_hp"]
    update_player(player["telegram_id"], player)
    await query.edit_message_text(
        f"💤 استراحت کردی. HP کامل پر شد ({player['max_hp']}).\n"
        f"🪙 -10 سکه (موجودی: {player['coins']})",
        reply_markup=city_keyboard(),
    )

def market_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ فروشگاه تجهیزات", callback_data="shop_weapons")],
        [InlineKeyboardButton("📚 کتابفروشی", callback_data="shop_books")],
        [InlineKeyboardButton("💎 فروشگاه آیتم و جواهرات", callback_data="shop_items")],
        [InlineKeyboardButton("⛓ بازار برده‌فروشی", callback_data="shop_slaves")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="city"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_market(query):
    await query.edit_message_text("🏪 **بازار سلستیا**\n\nخوش اومدی! چی میخوای؟", reply_markup=market_keyboard())

def simple_shop_keyboard(name, back_to="market"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛍 ورود به {name}", callback_data=f"enter_shop_{name}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=back_to),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_church(query):
    text = (
        "⛪️ **کلیسای نور**\n\n"
        "کشیش آریوس: «به کلیسای نور خوش آمدی، فرزند من. اینجا می‌تونی درمان بشی، "
        "سبک نبردت رو انتخاب کنی یا عوض کنی. هر بار تغییر کلاس، سطح از ۱ شروع میشه.»"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 درمان رایگان", callback_data="church_heal")],
        [InlineKeyboardButton("⚔️ تغییر سبک نبرد", callback_data="change_class")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="city"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

async def church_heal(query, player):
    player["hp"] = player["max_hp"]
    update_player(player["telegram_id"], player)
    await query.answer("💖 HP پر شد!", show_alert=True)

async def show_blacksmith(query):
    text = "⚒ **آهنگری ریشو**\n\n«خوش اومدی! میخوای آهنگری کنی یا سلاحت رو تعمیر کنم؟»"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 آهنگری", callback_data="forge")],
        [InlineKeyboardButton("🔧 تعمیر سلاح", callback_data="repair")],
        [InlineKeyboardButton("🧹 تمیز کردن", callback_data="clean")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="city"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb)

async def show_bank(query, player):
    now = int(time.time())
    elapsed = now - player.get("bank_time", now)
    interest = 0
    if player.get("bank_time"):
        interest = int(player["bank_coins"] * 0.03)
    text = (
        "🏦 **خزانه سلستیا**\n\n"
        f"💰 موجودی: {player['bank_coins']} سکه\n"
        f"📈 سود ۳٪ هر ۶ ساعت: +{interest} سکه (قابل برداشت)\n"
        f"⏰ زمان سپری‌شده: {elapsed // 3600} ساعت"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 سپرده‌گذاری", callback_data="bank_deposit"),
         InlineKeyboardButton("💸 برداشت", callback_data="bank_withdraw")],
        [InlineKeyboardButton("📥 دریافت سود", callback_data="bank_interest")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="city"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb)

# =====================================================
#  ⚔️ میدان نبرد
# =====================================================
def battle_field_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ دوئل", callback_data="duel_start"),
         InlineKeyboardButton("🗺 ماجراجویی", callback_data="adventure")],
        [InlineKeyboardButton("🕳 سیاه‌چال", callback_data="dungeon"),
         InlineKeyboardButton("✈️ سفر", callback_data="travel")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_battle_field(query):
    await query.edit_message_text("⚔️ **میدان نبرد**\n\nکجا میخوای بری؟", reply_markup=battle_field_keyboard())

# =====================================================
#  ⚔️ سیستم دوئل
# =====================================================
DUEL_QUEUE = {}

async def duel_start(query, player):
    DUEL_QUEUE[player["telegram_id"]] = {"player": player, "time": time.time()}
    await query.edit_message_text(
        "⚔️ **دنبال حریف می‌گردم...**\n\n⏳ تا ۳۰ ثانیه صبر کن.",
        reply_markup=back_and_close("battle_field"),
    )
    await asyncio.sleep(30)
    if player["telegram_id"] in DUEL_QUEUE:
        del DUEL_QUEUE[player["telegram_id"]]
        try:
            await query.edit_message_text("❌ کسی دنبال دوئل نیست.", reply_markup=battle_field_keyboard())
        except:
            pass

async def duel_find(query, context, player):
    for uid, info in list(DUEL_QUEUE.items()):
        if uid == player["telegram_id"]:
            continue
        other = info["player"]
        if abs(other["level"] - player["level"]) <= 3:
            del DUEL_QUEUE[uid]
            await do_duel(context, other, player)
            return True
    return False

async def do_duel(context, p1, p2):
    a = dict(p1); b = dict(p2)
    a_hp, b_hp = a["hp"], b["hp"]
    log = [f"⚔️ **دوئل!**\n\n👤 {a['name']} (L{a['level']})  VS  {b['name']} (L{b['level']})\n"]
    round_num = 1
    while a_hp > 0 and b_hp > 0 and round_num <= 30:
        log.append(f"\n— نوبت {round_num} —")
        for attacker, defender, a_hp_ref, d_hp_ref in [(a, b, [a_hp], [b_hp]), (b, a, [b_hp], [a_hp])]:
            if d_hp_ref[0] <= 0:
                break
            dmg = max(1, attacker["attack"] - defender["defense"] // 2 + random.randint(-2, 4))
            crit = random.random() < attacker["crit_hit"] / 100
            if crit:
                dmg = int(dmg * attacker["crit_dmg"])
            d_hp_ref[0] -= dmg
            log.append(f"⚔️ {attacker['name']} به {defender['name']} {dmg} دمیج زد")
        a_hp, b_hp = a_hp if a_hp < 100 else a_hp, b_hp
        round_num += 1
    if a_hp > 0 and b_hp <= 0:
        winner, loser = p1, p2
    elif b_hp > 0 and a_hp <= 0:
        winner, loser = p2, p1
    else:
        winner, loser = None, None
    if winner:
        add_xp(winner, 10)
        stolen = loser["coins"] // 3
        winner["coins"] += stolen
        loser["coins"] -= stolen
        winner["wins"] += 1
        loser["losses"] += 1
        winner["hp"] = max(1, a_hp if winner == p1 else b_hp)
        update_player(winner["telegram_id"], winner)
        update_player(loser["telegram_id"], loser)
        log.append(f"\n🏆 **{winner['name']} برنده شد!**\n⭐️ +10 تجربه و +{stolen} سکه")
    else:
        log.append("\n🤝 تساوی!")
    text = "\n".join(log)
    for p in [p1, p2]:
        try:
            await context.bot.send_message(chat_id=p["telegram_id"], text=text, parse_mode="Markdown")
        except:
            pass

# =====================================================
#  🕳 سیاه‌چال و ماجراجویی
# =====================================================
async def show_dungeon(query):
    text = (
        "🕳 **سیاه‌چال سلستیا**\n\n"
        "هر طبقه سخت‌تر از قبلی. در هر طبقه هیولا ظاهر میشه و باید شکستش بدی تا بری بالاتر.\n\n"
        "🎲 **باغ هزارتوعه** هم موجوده که شانسی تو رو به طبقات عجیب میندازه."
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ ورود به طبقه ۱", callback_data="dungeon_floor:1")],
        [InlineKeyboardButton("🎲 باغ هزارتوعه", callback_data="random_dungeon")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="battle_field"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb)

async def dungeon_floor(query, player, floor):
    monsters = load_monsters()
    if not monsters:
        await query.edit_message_text("❌ هنوز هیولایی تعریف نشده.", reply_markup=battle_field_keyboard())
        return
    candidates = [m for m in monsters.values() if m.get("level_min", 1) <= floor <= m.get("level_max", 100)]
    if not candidates:
        candidates = list(monsters.values())
    mon = random.choice(candidates).copy()
    mon["hp"] = mon.get("hp_max", 50)
    await run_battle(query, player, mon, f"طبقه {floor} سیاه‌چال")

async def random_dungeon(query, player):
    floor = random.choices(
        [random.randint(1, 10), random.randint(11, 30), random.randint(31, 50),
         random.randint(51, 70), random.randint(71, 90), random.randint(91, 100)],
        weights=[50, 25, 12, 7, 4, 2]
    )[0]
    await dungeon_floor(query, player, floor)

async def run_battle(query, player, mon, location_text=""):
    p_hp, p_atk, p_def, p_spd, p_crit_hit, p_crit_dmg = player["hp"], player["attack"], player["defense"], player["speed"], player["crit_hit"], player["crit_dmg"]
    m_hp, m_atk, m_def, m_spd = mon.get("hp_max", 50), mon.get("attack", 10), mon.get("defense", 10), mon.get("speed", 5)
    log = [f"⚔️ **نبرد در {location_text}!**\n\n👤 تو  VS  {mon.get('name','هیولا')}\n"]
    rnd = 1
    while p_hp > 0 and m_hp > 0 and rnd <= 30:
        log.append(f"\n— نوبت {rnd} —")
        first_p = p_spd >= m_spd
        for a_name, a_atk, a_spd, d_name, d_hp_ref, d_def in [
            (("تو", p_atk, p_spd, mon["name"], [m_hp], m_def) if first_p else (mon["name"], m_atk, m_spd, "تو", [p_hp], p_def)),
        ]:
            if d_hp_ref[0] <= 0: break
            dmg = max(1, a_atk - d_def // 2 + random.randint(-2, 4))
            crit = random.random() < (p_crit_hit / 100 if a_name == "تو" else 0.05)
            if crit and a_name == "تو":
                dmg = int(dmg * p_crit_dmg)
            d_hp_ref[0] -= dmg
            log.append(f"{'⚔️' if a_name=='تو' else '🗡'} {a_name} به {d_name} {dmg} دمیج زد")
        if first_p:
            m_hp = [m_hp][0]
            p_hp = [p_hp][0]
        else:
            m_hp = [m_hp][0]
            p_hp = [p_hp][0]
        rnd += 1
    if m_hp <= 0 and p_hp > 0:
        xp = mon.get("xp", 20)
        coins = mon.get("coins", 30)
        leveled = add_xp(player, xp)
        player["coins"] += coins
        drop_msg = ""
        if mon.get("drops") and random.random() < mon.get("drop_rate", 0.3):
            drop = random.choice(mon["drops"])
            player["inventory"].append(drop)
            drop_msg = f"\n🎁 دراپ: {drop}"
        player["wins"] += 1
        player["hp"] = max(1, p_hp)
        update_player(player["telegram_id"], player)
        log.append(f"\n🏆 **پیروزی!**\n⭐️ +{xp} تجربه و +{coins} سکه{drop_msg}")
        if leveled:
            log.append(f"\n🎉 لِوِل آپ! رسیدی به سطح {player['level']}")
    elif p_hp <= 0:
        player["losses"] += 1
        player["hp"] = max(1, player["max_hp"] // 2)
        update_player(player["telegram_id"], player)
        log.append(f"\n💀 شکست خوردی! HP به {player['hp']} برگشت")
    else:
        log.append("\n⏱ نبرد طولانی شد!")
    await query.edit_message_text("\n".join(log), reply_markup=battle_field_keyboard())

async def show_adventure(query):
    text = "🗺 **ماجراجویی**\n\nکجا میخوای بری؟"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕳 سیاه‌چال", callback_data="dungeon"),
         InlineKeyboardButton("🎲 باغ هزارتوعه", callback_data="random_dungeon")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="battle_field"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb)

async def show_travel(query):
    await query.edit_message_text("✈️ **سفر**\n\n⛔️ این بخش فعلاً بسته است.", reply_markup=back_and_close("battle_field"))
 
#  🎒 کوله‌بار
# =====================================================
async def show_inventory(query, player):
    if not player["inventory"]:
        text = "🎒 **کوله‌بار**\n\nخالیه!"
    else:
        items = {}
        for it in player["inventory"]:
            items[it] = items.get(it, 0) + 1
        text = "🎒 **کوله‌بار**\n\n"
        for it, count in items.items():
            text += f"• `{it}` (x{count}) — [عملیات](callback:item_use:{it})\n"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

# =====================================================
#  🏛 انجمن
# =====================================================
def guild_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚜ مأموریت‌ها", callback_data="missions")],
        [InlineKeyboardButton("🔅 تشکیل اتحاد", callback_data="create_guild")],
        [InlineKeyboardButton("🏆 لیست برترین‌ها", callback_data="leaderboard")],
        [InlineKeyboardButton("👥 دوستان", callback_data="friends")],
        [InlineKeyboardButton("🎁 هدیه دادن", callback_data="gift")],
        [InlineKeyboardButton("📜 قوانین", callback_data="rules")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="home"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_guild_menu(query):
    await query.edit_message_text("🏛 **انجمن ماجراجویان**\n\nیکی از گزینه‌ها رو انتخاب کن:", reply_markup=guild_menu_keyboard())

async def show_missions(query):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚜ اصلی (تجربه)", callback_data="mission_main")],
        [InlineKeyboardButton("🔸 فرعی (سکه و آیتم)", callback_data="mission_side")],
        [InlineKeyboardButton("📋 درخواست‌های ماجراجویان", callback_data="party_requests")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="guild_menu"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])
    await query.edit_message_text("⚜ **مأموریت‌ها**\n\nکدوم؟", reply_markup=kb)

async def show_leaderboard(query):
    players = load_players()
    sorted_p = sorted(players.values(), key=lambda x: (x["wins"], x["xp"]), reverse=True)[:10]
    text = "🏆 **۱۰ ماجراجوی برتر**\n\n"
    for i, p in enumerate(sorted_p, 1):
        text += f"{i}. {p['name']} — سطح {p['level']} — برد: {p['wins']}\n"
    await query.edit_message_text(text, reply_markup=back_and_close("guild_menu"))

async def show_rules(query):
    text = (
        "📜 **قوانین سلستیا**\n\n"
        "1️⃣ احترام به بازیکنان دیگر\n"
        "2️⃣ هرگونه تقلب و اکسپلویت ممنوع\n"
        "3️⃣ استفاده از چند اکانت ممنوع\n"
        "4️⃣ تبعید توسط ادمین غیرقابل بازگشت\n"
        "5️⃣ قوانین انجمن و اتحادها بر اساس توافق اعضا\n"
        "6️⃣ هر گونه خشونت در چت ممنوع\n"
        "7️⃣ اسپم و تبلیغات ممنوع"
    )
    await query.edit_message_text(text, reply_markup=back_and_close("guild_menu"))

# =====================================================
#  🔑 ساخت اکانت دائمی
# =====================================================
async def create_permanent_start(query, context):
    context.user_data["creating_account"] = {"step": "username"}
    await query.edit_message_text(
        "🔑 **ساخت اکانت دائمی**\n\n"
        "یه نام کاربری انتخاب کن (مثلاً `ali123`):",
        reply_markup=back_keyboard("settings"),
    )

async def handle_permanent_creation(update, context, player):
    step_data = context.user_data.get("creating_account")
    if not step_data:
        return
    text = update.message.text.strip()
    if step_data["step"] == "username":
        if len(text) < 3:
            await update.message.reply_text("❌ نام کاربری باید حداقل ۳ حرف باشه.")
            return
        players = load_players()
        for p in players.values():
            if p.get("username_login") == text:
                await update.message.reply_text("❌ این نام کاربری قبلاً گرفته شده.")
                return
        step_data["username"] = text
        step_data["step"] = "password"
        await update.message.reply_text("🔒 حالا یه رمز عبور انتخاب کن:")
    elif step_data["step"] == "password":
        if len(text) < 4:
            await update.message.reply_text("❌ رمز باید حداقل ۴ حرف باشه.")
            return
        player["username_login"] = step_data["username"]
        player["password"] = text
        update_player(player["telegram_id"], player)
        context.user_data["creating_account"] = None
        await update.message.reply_text(
            f"✅ اکانت دائمی ساخته شد!\n\n👤 نام کاربری: `{step_data['username']}`\n🔒 رمز: `{text}`",
            reply_markup=settings_keyboard(),
            parse_mode="Markdown",
        )

# =====================================================
#  🗼 پنل ادمین (برج خدایان)
# =====================================================
def god_tower_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏯ انجماد زمان", callback_data="freeze_toggle")],
        [InlineKeyboardButton("🪬 دست خداوند", callback_data="god_hand")],
        [InlineKeyboardButton("⚖️ داوری الهی", callback_data="divine_judge")],
        [InlineKeyboardButton("🚪 خروج از برج", callback_data="exit_god_tower")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="settings"),
         InlineKeyboardButton("❌ بستن", callback_data="close")],
    ])

async def show_god_tower(query, user_id):
    if not is_admin(user_id):
        await query.answer("⛔️ فقط ادمین.", show_alert=True)
        return
    await query.edit_message_text(
        "🗼 **برج خدایان**\n\nبه پنل مدیریت خوش اومدی.",
        reply_markup=god_tower_keyboard(),
    )

async def freeze_toggle(query, context):
    if not is_admin(query.from_user.id):
        return
    data = load_frozen()
    data["frozen"] = not data.get("frozen", False)
    save_frozen(data)
    state = "فعال" if data["frozen"] else "غیرفعال"
    await query.edit_message_text(
        f"⏯ انجماد زمان: **{state}**\n\nربات {'متوقف' if data['frozen'] else 'فعال'} شد.",
        reply_markup=god_tower_keyboard(),
        parse_mode="Markdown",
    )

def god_hand_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 خلقت", callback_data="creation")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="god_tower")],
    ])

def creation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ خلق آیتم", callback_data="create_item")],
        [InlineKeyboardButton("🐉 خلق موجود", callback_data="create_monster")],
        [InlineKeyboardButton("🪨 خلق مواد", callback_data="create_material")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="god_hand")],
    ])

async def god_hand(query):
    if not is_admin(query.from_user.id):
        return
    await query.edit_message_text("🪬 **دست خداوند**\n\nیکی از گزینه‌ها:", reply_markup=god_hand_keyboard())

async def creation_menu(query):
    if not is_admin(query.from_user.id):
        return
    await query.edit_message_text("🛠 **خلقت**\n\nچی میخوای بسازی؟", reply_markup=creation_keyboard())

async def start_create_item(query, context):
    if not is_admin(query.from_user.id):
        return
    context.user_data["creating"] = {"type": "item", "step": "name"}
    await query.edit_message_text(
        "⚔️ **خلق آیتم**\n\nنام آیتم رو بفرست:\n\n"
        "📋 **فرمت (با | از هم جدا کن):**\n"
        "`نام | رنگ | سطح | قدرت | دفاع | Crit DMG | Crit Hit | قیمت | درجه کمیابی | محل تجهیز | حداقل سطح | توضیحات`\n\n"
        "مثال:\n"
        "`کمان نورانی | 🔴 | سطح الهی | 1000 | 100 | 1.5 | 25 | 1000 | الهی | دست | 50 | کمانی از نور خالص`",
        reply_markup=back_keyboard("creation"),
    )

async def start_create_monster(query, context):
    if not is_admin(query.from_user.id):
        return
    context.user_data["creating"] = {"type": "monster", "step": "name"}
    await query.edit_message_text(
        "🐉 **خلق موجود**\n\nنام موجود رو بفرست:\n\n"
        "📋 **فرمت (با | از هم جدا کن):**\n"
        "`نام | سطح | حمله | دفاع | سرعت | مانا | HP | XP | سکه | شانس دراپ | آیتم‌ها(با -) | سلاح`\n\n"
        "مثال:\n"
        "`اژدهای آتشین | 🔴 سطح عذاب | 500 | 300 | 50 | 100 | 2000 | 1000 | 500 | 0.7 | شمشیر آتشین-قلب اژدها-پولک طلا | شمشیر آتشین`",
        reply_markup=back_keyboard("creation"),
    )

async def start_create_material(query, context):
    if not is_admin(query.from_user.id):
        return
    context.user_data["creating"] = {"type": "material", "step": "name"}
    await query.edit_message_text(
        "🪨 **خلق مواد**\n\nنام ماده رو بفرست:\n\n"
        "📋 **فرمت (با | از هم جدا کن):**\n"
        "`نام | درجه کمیابی | قیمت | محل پیدا شدن`\n\n"
        "مثال:\n"
        "`سنگ تنگستن | 🟠 سطح افسانه‌ای | 500 | ماجراجویی 10%، طبقه 10-20 دانجن 5%`",
        reply_markup=back_keyboard("creation"),
    )

async def process_creation(update, context):
    data = context.user_data.get("creating")
    if not data:
        return
    text = update.message.text.strip()
    if data["type"] == "item":
        try:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) < 12:
                await update.message.reply_text("❌ تعداد فیلد کمتر از ۱۲ تاست. دوباره بفرست.")
                return
            items = load_items()
            item_id = f"item_{len(items) + 1}"
            items[item_id] = {
                "name": parts[0], "color": parts[1], "rarity": parts[2],
                "attack": int(parts[3]), "defense": int(parts[4]),
                "crit_dmg": float(parts[5]), "crit_hit": int(parts[6]),
                "price": int(parts[7]), "rarity_text": parts[8],
                "slot": parts[9], "min_level": int(parts[10]),
                "description": parts[11], "type": "item",
            }
            save_items(items)
            context.user_data["creating"] = None
            await update.message.reply_text(
                f"✅ آیتم `{parts[0]}` ساخته شد!",
                parse_mode="Markdown",
                reply_markup=creation_keyboard(),
            )
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {e}\n\nفرمت رو درست وارد کن.")
    elif data["type"] == "monster":
        try:
            parts = [p.strip() for p in text.split("|")]
            monsters = load_monsters()
            mon_id = f"mon_{len(monsters) + 1}"
            monsters[mon_id] = {
                "name": parts[0], "level_text": parts[1],
                "attack": int(parts[2]), "defense": int(parts[3]),
                "speed": int(parts[4]), "mana": int(parts[5]),
                "hp_max": int(parts[6]), "xp": int(parts[7]),
                "coins": int(parts[8]), "drop_rate": float(parts[9]),
                "drops": parts[10].split("-") if len(parts) > 10 else [],
                "weapon": parts[11] if len(parts) > 11 else None,
                "type": "monster",
            }
            save_monsters(monsters)
            context.user_data["creating"] = None
            await update.message.reply_text(
                f"✅ موجود `{parts[0]}` ساخته شد!",
                reply_markup=creation_keyboard(),
            )
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {e}")
    elif data["type"] == "material":
        try:
            parts = [p.strip() for p in text.split("|")]
            materials = load_materials()
            mat_id = f"mat_{len(materials) + 1}"
            materials[mat_id] = {
                "name": parts[0], "rarity": parts[1],
                "price": int(parts[2]), "drop_locations": parts[3] if len(parts) > 3 else "",
                "type": "material",
            }
            save_materials(materials)
            context.user_data["creating"] = None
            await update.message.reply_text(
                f"✅ ماده `{parts[0]}` ساخته شد!",
                reply_markup=creation_keyboard(),
            )
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {e}")

async def divine_judge(query):
    if not is_admin(query.from_user.id):
        return
    players = load_players()
    text = "⚖️ **داوری الهی**\n\nلیست بازیکنان:\n\n"
    buttons = []
    for uid, p in list(players.items())[:15]:
        status = "🟢" if p.get("online") else "⚫"
        text += f"{status} `{p['telegram_id']}` — {p['name']} — سطح {p['level']}\n"
        buttons.append([InlineKeyboardButton(f"{status} {p['name']}", callback_data=f"judge_{p['telegram_id']}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="god_tower")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def judge_user(query, target_id):
    if not is_admin(query.from_user.id):
        return
    players = load_players()
    target = players.get(str(target_id))
    if not target:
        await query.answer("❌ پیدا نشد.", show_alert=True)
        return
    text = format_profile(target)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ برکت الهی", callback_data=f"bless_{target_id}")],
        [InlineKeyboardButton("⛓ نفرین زنجیر ابدی", callback_data=f"curse_{target_id}")],
        [InlineKeyboardButton("💀 حکم تبعید", callback_data=f"ban_{target_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="divine_judge")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

async def bless_user(query, target_id):
    if not is_admin(query.from_user.id):
        return
    await query.edit_message_text(
        f"✨ **برکت الهی**\n\nچند سکه میخوای بدی به بازیکن `{target_id}`؟\n\nعدد بفرست:",
        reply_markup=back_keyboard(f"judge_{target_id}"),
    )
    context_user_data = {"blessing_target": target_id}

async def curse_user(query, target_id):
    if not is_admin(query.from_user.id):
        return
    players = load_players()
    target = players.get(str(target_id))
    if target:
        target["level_blocked"] = True
        update_player(target_id, target)
    await query.answer("⛓ نفرین اعمال شد. سطحش بلاکه.", show_alert=True)
    await judge_user(query, target_id)

async def ban_user(query, target_id):
    if not is_admin(query.from_user.id):
        return
    players = load_players()
    target = players.get(str(target_id))
    if target:
        target["banned"] = True
        update_player(target_id, target)
    await query.edit_message_text(
        f"💀 **حکم تبعید صادر شد!**\n\nبازیکن `{target_id}` از ربات تبعید شد.",
        reply_markup=god_tower_keyboard(),
    )

# ==========================================
