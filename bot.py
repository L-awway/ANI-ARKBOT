import telebot
from telebot import types
import json
import os
from datetime import datetime, timezone, timedelta

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8813006955:AAHYH-WEmw5E8Z9h9ZPGhHSHMR-yAnz2yoM"
OWNER_ID = 7080227092

DATA_FILE = "scores.json"
QUESTIONS_FILE = "questions_count.json"
ADMINS_FILE = "admins.json"
NICKS_FILE = "nicks.json"
LIMITS_FILE = "daily_limits.json"
ANICARD_FILE = "anibattle_gifts.json"
# =====================

bot = telebot.TeleBot(BOT_TOKEN)

# ===== ПРОВЕРКА ФАЙЛОВ =====
def ensure_files_exist():
    for f, default in [
        (ADMINS_FILE, {"admins": []}),
        (DATA_FILE, {}),
        (QUESTIONS_FILE, {"count": 0}),
        (NICKS_FILE, {}),
        (LIMITS_FILE, {}),
        (ANICARD_FILE, {"gifts": []}),
    ]:
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as file:
                json.dump(default, file, indent=2, ensure_ascii=False)

ensure_files_exist()

# ===== РАБОТА С ФАЙЛАМИ =====
def load_json(file, key=None):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if key:
                return data.get(key, [])
            return data
    except:
        return {} if not key else []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===== МСК ВРЕМЯ =====
def get_msk_date():
    msk = timezone(timedelta(hours=3))
    return datetime.now(msk).strftime("%Y-%m-%d")

# ===== ЛИМИТЫ =====
def check_limit(username):
    clean = username.lower().replace('@', '')
    today = get_msk_date()
    limits = load_json(LIMITS_FILE)
    
    if clean not in limits or limits[clean].get("date") != today:
        return True, 5
    
    count = limits[clean].get("count", 0)
    if count >= 5:
        return False, 0
    return True, 5 - count

def add_limit(username):
    clean = username.lower().replace('@', '')
    today = get_msk_date()
    limits = load_json(LIMITS_FILE)
    
    if clean not in limits or limits[clean].get("date") != today:
        limits[clean] = {"date": today, "count": 1}
    else:
        limits[clean]["count"] += 1
    
    save_json(LIMITS_FILE, limits)

# ============================================================
# РАБОТА С АДМИНАМИ (ЧЕРЕЗ USERNAME)
# ============================================================

OWNER_USERNAME = "Zhongli_3112"  # твой username без @

def load_admins():
    """Загружает список username'ов админов"""
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            admins = data.get("admins", [])
            print(f"📖 load_admins: {admins}")
            return admins
    except Exception as e:
        print(f"❌ load_admins error: {e}")
        return []

def save_admins(admins):
    """Сохраняет список username'ов админов"""
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({"admins": admins}, f, indent=2, ensure_ascii=False)
    print(f"💾 save_admins: {admins}")

def is_owner_username(username):
    """Проверяет, является ли username владельцем"""
    if not username:
        return False
    return username.lower() == OWNER_USERNAME.lower()

def is_admin_username(username):
    """Проверяет, является ли username админом"""
    if not username:
        return False
    if is_owner_username(username):
        return True
    admins = load_admins()
    return username.lower() in [a.lower() for a in admins]

def is_owner_or_admin(message):
    """Проверяет по сообщению"""
    username = message.from_user.username
    return is_owner_username(username) or is_admin_username(username)

# ===== РАБОТА С КЛИЧКАМИ =====
def load_nicks():
    return load_json(NICKS_FILE)

def save_nicks(nicks):
    save_json(NICKS_FILE, nicks)

def get_display_name(username):
    nicks = load_nicks()
    clean = username.lower().replace('@', '')
    return nicks.get(clean, clean)

# ===== БАЛЛЫ =====
def load_scores():
    return load_json(DATA_FILE)

def save_scores(scores):
    save_json(DATA_FILE, scores)

scores = load_scores()

# ============================================================
# КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['vstart'])
def vstart(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏆 Таблица"),
        types.KeyboardButton("🎁 Подарки"),
        types.KeyboardButton("👥 Админы"),
        types.KeyboardButton("📖 Помощь")
    )
    bot.reply_to(
        message,
        "🤖 *Добро пожаловать в викторину канала ANIARK!*\n\n"
        "📌 *Все команды начинаются с `/v`*\n\n"
        "📊 *Основные:*\n"
        "`/vstart` — это меню\n"
        "`/vtop` — таблица лидеров\n"
        "`/vgifts` — список подарков\n\n"
        "Для админов:\n"
        "`/vadd @user` — начислить балл\n"
        "`/vadd @user 3` — начислить 3 балла\n"
        "`/vnick @user Кличка` — дать кличку\n\n"
        "💡 Лимит: *5 ответов в день* на человека (МСК)",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['vhelp'])
def vhelp(message):
    bot.reply_to(
        message,
        "📖 *СПРАВКА*\n\n"
        "*Для всех:*\n"
        "`/vstart` — меню\n"
        "`/vtop` — таблица\n"
        "`/vadmins_list` — список админов\n"
        "`/vgifts` — подарки\n\n"
        "*Для админов:*\n"
        "`/vadd @user [N]` — баллы\n"
        "`/vremove @user [N]` — отнять\n"
        "`/vdelete @user` — удалить\n"
        "`/vnick @user Кличка` — кличка\n"
        "`/vnick_remove @user` — убрать кличку\n"
        "`/vquestion` — +1 вопрос\n"
        "`/vquestions_remove N` — убрать N\n"
        "`/vquestions_set N` — установить\n"
        "`/vadd_card 90 Сид 100` — добавить карту\n"
        "`/vremove_card 90` — удалить карту\n\n"
        "*Только для владельца:*\n"
        "`/vadd_admin @user` — добавить админа\n"
        "`/vremove_admin @user` — удалить админа\n"
        "`/vreset` — сброс\n\n",
        parse_mode="Markdown"
    )

# ===== /vtop =====
@bot.message_handler(commands=['vtop'])
def vtop(message):
    filtered = {k: v for k, v in scores.items() if v > 0}
    if not filtered:
        bot.reply_to(message, "📭 *Таблица пуста*", parse_mode="Markdown")
        return
    
    sorted_users = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    questions = load_json(QUESTIONS_FILE).get("count", 0)
    
    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*\n"
    text += f"❓ Вопросов: {questions}\n"
    text += f"👥 Участников: {len(filtered)}\n\n"
    
    for i, (user, score) in enumerate(sorted_users, 1):
        name = get_display_name(user)
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        text += f"{medal} {name} — {score}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ===== /vadd =====
@bot.message_handler(commands=['vadd'])
def vadd(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    username = None
    points = 1
    
    for part in parts:
        if part.startswith('@') and len(part) > 1:
            username = part.lower()
            break
    
    if not username and message.reply_to_message:
        user = message.reply_to_message.from_user
        if user.username:
            username = "@" + user.username.lower()
        else:
            username = user.first_name or f"user_{user.id}"
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username или ответьте на сообщение.")
        return
    
    for part in parts:
        try:
            num = int(part)
            if num > 0:
                points = num
                break
        except ValueError:
            continue
    
    clean = username.replace('@', '').lower()
    
    can, remaining = check_limit(clean)
    if not can:
        bot.reply_to(
            message,
            f"❌ *{username}* уже ответил на 5 вопросов сегодня.\n"
            f"Лимит обновится в 00:00 (МСК).",
            parse_mode="Markdown"
        )
        return
    
    scores[clean] = scores.get(clean, 0) + points
    save_scores(scores)
    add_limit(clean)
    
    can2, remaining2 = check_limit(clean)
    word = "балл" if points == 1 else "балла" if points in [2,3,4] else "баллов"
    name = get_display_name(clean)
    bot.reply_to(
        message,
        f"✅ {name} +{points} {word}! Всего: {scores[clean]}\n"
        f"📊 Осталось ответов сегодня: {remaining2}/5",
        parse_mode="Markdown"
    )

# ===== /vremove =====
@bot.message_handler(commands=['vremove'])
def vremove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    username = None
    points = 1
    
    for part in parts:
        if part.startswith('@') and len(part) > 1:
            username = part.lower()
            break
    
    if not username and message.reply_to_message:
        user = message.reply_to_message.from_user
        if user.username:
            username = "@" + user.username.lower()
        else:
            username = user.first_name or f"user_{user.id}"
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username или ответьте на сообщение.")
        return
    
    for part in parts:
        try:
            num = int(part)
            if num > 0:
                points = num
                break
        except ValueError:
            continue
    
    clean = username.replace('@', '').lower()
    if clean not in scores:
        bot.reply_to(message, f"❌ У {username} нет баллов.")
        return
    
    scores[clean] = max(0, scores[clean] - points)
    save_scores(scores)
    name = get_display_name(clean)
    bot.reply_to(message, f"➖ {name} -{points} баллов. Осталось: {scores[clean]}")

# ===== /vdelete =====
@bot.message_handler(commands=['vdelete'])
def vdelete(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    username = None
    
    for part in parts:
        if part.startswith('@') and len(part) > 1:
            username = part.lower()
            break
    
    if not username and message.reply_to_message:
        user = message.reply_to_message.from_user
        if user.username:
            username = "@" + user.username.lower()
        else:
            username = user.first_name or f"user_{user.id}"
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username.")
        return
    
    clean = username.replace('@', '').lower()
    if clean not in scores:
        bot.reply_to(message, f"❌ Пользователь не найден.")
        return
    
    del scores[clean]
    save_scores(scores)
    
    nicks = load_nicks()
    if clean in nicks:
        del nicks[clean]
        save_nicks(nicks)
    
    bot.reply_to(message, f"🗑️ {username} удалён.")

# ===== /vnick =====
@bot.message_handler(commands=['vnick'])
def vnick(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используйте: `/vnick @user Кличка`", parse_mode="Markdown")
        return
    
    username = parts[1].lower()
    if not username.startswith('@'):
        bot.reply_to(message, "❌ Укажите @username")
        return
    
    clean = username.replace('@', '')
    new_nick = " ".join(parts[2:])
    
    nicks = load_nicks()
    nicks[clean] = new_nick
    save_nicks(nicks)
    
    bot.reply_to(message, f"✅ {username} → *{new_nick}*", parse_mode="Markdown")

# ===== /vnick_remove =====
@bot.message_handler(commands=['vnick_remove'])
def vnick_remove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/vnick_remove @user`", parse_mode="Markdown")
        return
    
    username = parts[1].lower()
    clean = username.replace('@', '')
    
    nicks = load_nicks()
    if clean not in nicks:
        bot.reply_to(message, f"⚠️ У {username} нет клички.")
        return
    
    del nicks[clean]
    save_nicks(nicks)
    bot.reply_to(message, f"✅ Кличка {username} удалена.")

# ===== /vquestion =====
@bot.message_handler(commands=['vquestion'])
def vquestion(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    data = load_json(QUESTIONS_FILE)
    data["count"] = data.get("count", 0) + 1
    save_json(QUESTIONS_FILE, data)
    bot.reply_to(message, f"❓ Вопрос засчитан! Всего: *{data['count']}*", parse_mode="Markdown")

# ===== /vquestions_remove =====
@bot.message_handler(commands=['vquestions_remove'])
def vquestions_remove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/vquestions_remove N`", parse_mode="Markdown")
        return
    
    try:
        n = int(parts[1])
        if n <= 0:
            bot.reply_to(message, "❌ Число > 0")
            return
    except:
        bot.reply_to(message, "❌ Введите число")
        return
    
    data = load_json(QUESTIONS_FILE)
    data["count"] = max(0, data.get("count", 0) - n)
    save_json(QUESTIONS_FILE, data)
    bot.reply_to(message, f"➖ Убрано {n}. Всего: *{data['count']}*", parse_mode="Markdown")

# ===== /vquestions_set =====
@bot.message_handler(commands=['vquestions_set'])
def vquestions_set(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/vquestions_set N`", parse_mode="Markdown")
        return
    
    try:
        n = int(parts[1])
        if n < 0:
            bot.reply_to(message, "❌ Число >= 0")
            return
    except:
        bot.reply_to(message, "❌ Введите число")
        return
    
    save_json(QUESTIONS_FILE, {"count": n})
    bot.reply_to(message, f"✅ Установлено: *{n}*", parse_mode="Markdown")

# ============================================================
# КОМАНДЫ АДМИНОВ
# ============================================================

# ===== ДОБАВИТЬ ПО USERNAME =====
@bot.message_handler(commands=['vadd_admin'])
def vadd_admin(message):
    if not is_owner_username(message.from_user.username):
        bot.reply_to(message, "⛔ Только владелец может добавлять админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].startswith('@'):
        bot.reply_to(message, "❌ Используйте: `/vadd_admin @username`", parse_mode="Markdown")
        return
    
    username = parts[1].lstrip('@')
    admins = load_admins()
    
    if username.lower() in [a.lower() for a in admins]:
        bot.reply_to(message, f"⚠️ @{username} уже админ.")
        return
    
    admins.append(username)
    save_admins(admins)
    bot.reply_to(
        message,
        f"✅ {username} добавлен как админ!\n"
        f"📊 Всего админов: {len(admins)}"
    )

# ===== УДАЛИТЬ ПО USERNAME =====
@bot.message_handler(commands=['vremove_admin'])
def vremove_admin(message):
    if not is_owner_username(message.from_user.username):
        bot.reply_to(message, "⛔ Только владелец может удалять админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].startswith('@'):
        bot.reply_to(message, "❌ Используйте: `/vremove_admin @username`", parse_mode="Markdown")
        return
    
    username = parts[1].lstrip('@')
    admins = load_admins()
    
    found = None
    for a in admins:
        if a.lower() == username.lower():
            found = a
            break
    
    if not found:
        bot.reply_to(message, f"⚠️ @{username} не найден в админах.")
        return
    
    admins.remove(found)
    save_admins(admins)
    bot.reply_to(
        message,
        f"✅ {username} удалён из админов.\n"
        f"📊 Всего админов: {len(admins)}"
    )

# ===== СПИСОК АДМИНОВ (ВИДЯТ ВСЕ) =====
@bot.message_handler(commands=['vadmins_list'])
def vadmins_list(message):
    admins = load_admins()
    text = "👥 *СПИСОК АДМИНОВ*\n\n"
    text += f"👑 *Владелец:* {OWNER_USERNAME}\n\n"
    
    if not admins:
        text += "📭 *Добавленных админов нет.*"
    else:
        text += f"🛡️ *Админы ({len(admins)}):*\n"
        for i, username in enumerate(admins, 1):
            # Просто выводим username как есть — подчёркивания сохранятся
            text += f"{i}. {username}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ============================================================
# ПОДАРКИ (ANICARD)
# ============================================================

def get_gift_emoji(rating):
    r = int(rating)
    if 98 <= r <= 100:
        return "🟣"
    elif 87 <= r <= 90:
        return "🔵"
    elif 79 <= r <= 80:
        return "🟢"
    else:
        return "⚪"

@bot.message_handler(commands=['vadd_card'])
def vadd_card(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    # Формат: /vadd_card РЕЙТИНГ НАЗВАНИЕ ЦЕНА
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ Используйте: `/vadd_card 90 Сид 100`\n(рейтинг, название, цена)", parse_mode="Markdown")
        return
    
    try:
        rating = int(parts[1])
        price = int(parts[-1])
        name = " ".join(parts[2:-1])
    except:
        bot.reply_to(message, "❌ Рейтинг и цена должны быть числами.")
        return
    
    if rating < 1 or rating > 100:
        bot.reply_to(message, "❌ Рейтинг от 1 до 100")
        return
    if price < 1:
        bot.reply_to(message, "❌ Цена > 0")
        return
    
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    for g in gifts:
        if g["name"].lower() == name.lower():
            bot.reply_to(message, f"⚠️ Карта с таким названием уже есть.")
            return
    
    gifts.append({"rating": rating, "name": name, "price": price})
    gifts.sort(key=lambda x: x["price"], reverse=True)
    data["gifts"] = gifts
    save_json(ANICARD_FILE, data)
    
    emoji = get_gift_emoji(rating)
    bot.reply_to(message, f"✅ Добавлено: {emoji} {rating} — {name} — {price} 🪙")

@bot.message_handler(commands=['vremove_card'])
def vremove_card(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ `/vremove_card 90` (рейтинг)", parse_mode="Markdown")
        return
    
    try:
        rating = int(parts[1])
    except:
        bot.reply_to(message, "❌ Введите рейтинг числом")
        return
    
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    found = False
    new_gifts = []
    for g in gifts:
        if g["rating"] == rating:
            found = True
        else:
            new_gifts.append(g)
    
    if not found:
        bot.reply_to(message, f"⚠️ Карта с рейтингом {rating} не найдена.")
        return
    
    data["gifts"] = new_gifts
    save_json(ANICARD_FILE, data)
    bot.reply_to(message, f"✅ Карта с рейтингом {rating} удалена.")

@bot.message_handler(commands=['vanicard'])
def vanicard(message):
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    if not gifts:
        bot.reply_to(message, "📭 *Список AniCard пуст*", parse_mode="Markdown")
        return
    
    text = "🎁 *ПОДАРКИ ANICARD*\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for g in gifts:
        emoji = get_gift_emoji(g["rating"])
        text += f"{emoji} *{g['rating']}* — {g['name']} — {g['price']} 🪙\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['vstars'])
def vstars(message):
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    # Фильтруем: только карты с ценой >= 15, сортируем по цене (убывание)
    filtered = [g for g in gifts if g.get("price", 0) >= 15]
    filtered.sort(key=lambda x: x["price"], reverse=True)
    
    if not filtered:
        bot.reply_to(message, "📭 *Список Telegram-звёзд пуст*\n(карт с ценой ≥ 15 нет)", parse_mode="Markdown")
        return
    
    text = "⭐ *ПОДАРКИ TELEGRAM (звёзды)*\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, g in enumerate(filtered, 1):
        text += f"🏆 Место {i} → ⭐ {g['price']} звёзд ({g['name']})\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['vgifts'])
def vgifts(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎁 AniCard", callback_data="gift_anicard"),
        types.InlineKeyboardButton("⭐ Telegram", callback_data="gift_stars")
    )
    bot.reply_to(message, "🎁 *Выберите список подарков:*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["gift_anicard", "gift_stars"])
def callback_gifts(call):
    if call.data == "gift_anicard":
        vanicard(call.message)
    else:
        vstars(call.message)
    bot.answer_callback_query(call.id)

# ===== /vreset =====
@bot.message_handler(commands=['vreset'])
def vreset(message):
    if not is_owner_username(message.from_user.username):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    global scores
    scores = {}
    save_scores(scores)
    save_json(QUESTIONS_FILE, {"count": 0})
    save_nicks({})
    save_json(LIMITS_FILE, {})
    bot.reply_to(message, "🗑️ Всё сброшено!")

# ============================================================
# КНОПКИ
# ============================================================

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    
    if text == "🏆 Таблица":
        vtop(message)
    elif text == "🎁 Подарки":
        vgifts(message)
    elif text == "👥 Админы":
        vadmins_list(message)
    elif text == "📖 Помощь":
        vhelp(message)

# ============================================================
# ЗАПУСК
# ============================================================

print("✅ Викторина-бот запущен!")
print(f"👑 Владелец: @{OWNER_USERNAME}")
print("=" * 40)
bot.infinity_polling()
