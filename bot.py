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
STARS_FILE = "telegram_gifts.json"
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
        (STARS_FILE, {"gifts": []})
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
    """Возвращает текущую дату по МСК"""
    msk = timezone(timedelta(hours=3))
    return datetime.now(msk).strftime("%Y-%m-%d")

# ===== ЛИМИТЫ =====
def check_limit(username):
    """Проверяет, может ли пользователь ещё отвечать сегодня. Возвращает (можно, сколько_осталось)"""
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
    """Увеличивает счётчик ответов пользователя"""
    clean = username.lower().replace('@', '')
    today = get_msk_date()
    limits = load_json(LIMITS_FILE)
    
    if clean not in limits or limits[clean].get("date") != today:
        limits[clean] = {"date": today, "count": 1}
    else:
        limits[clean]["count"] += 1
    
    save_json(LIMITS_FILE, limits)

# ===== РАБОТА С АДМИНАМИ =====
def load_admins():
    return load_json(ADMINS_FILE, "admins")

def save_admins(admins):
    save_json(ADMINS_FILE, {"admins": admins})

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in load_admins()

def is_owner_or_admin(message):
    uid = message.from_user.id
    return is_owner(uid) or is_admin(uid)

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
        "`/vadd_card 92 Название` — добавить карту\n"
        "`/vadd_card_remove 92` — удалить карту\n"
        "`/vadd_stars 1 100` — звёзды за место\n"
        "`/vadd_stars_remove 1` — убрать место\n\n"
        "*Только для владельца:*\n"
        "`/vadd_admin_id 123456789` — админ по ID\n"
        "`/vadd_admin @user` — админ по @\n"
        "`/vremove_admin_id 123456789` — убрать\n"
        "`/vremove_admin @user` — убрать\n"
        "`/vadmins_list` — список\n"
        "`/vreset` — сброс",
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
    
    # ПРОВЕРКА ЛИМИТА
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
# АДМИНЫ
# ============================================================

@bot.message_handler(commands=['vadd_admin_id'])
def vadd_admin_id(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ `/vadd_admin_id 123456789`", parse_mode="Markdown")
        return
    
    try:
        uid = int(parts[1])
        if uid == OWNER_ID:
            bot.reply_to(message, "👑 Владелец уже админ.")
            return
        admins = load_admins()
        if uid in admins:
            bot.reply_to(message, f"⚠️ ID {uid} уже админ.")
            return
        admins.append(uid)
        save_admins(admins)
        bot.reply_to(message, f"✅ ID `{uid}` добавлен как админ!", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Введите корректный ID")

@bot.message_handler(commands=['vremove_admin_id'])
def vremove_admin_id(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ `/vremove_admin_id 123456789`", parse_mode="Markdown")
        return
    
    try:
        uid = int(parts[1])
        admins = load_admins()
        if uid not in admins:
            bot.reply_to(message, f"⚠️ ID {uid} не админ.")
            return
        admins.remove(uid)
        save_admins(admins)
        bot.reply_to(message, f"✅ ID `{uid}` удалён.", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Введите корректный ID")

@bot.message_handler(commands=['vadd_admin'])
def vadd_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].startswith('@'):
        bot.reply_to(message, "❌ `/vadd_admin @username`", parse_mode="Markdown")
        return
    
    try:
        user = bot.get_chat(parts[1])
        uid = user.id
        if uid == OWNER_ID:
            bot.reply_to(message, "👑 Владелец уже админ.")
            return
        admins = load_admins()
        if uid in admins:
            bot.reply_to(message, f"⚠️ {parts[1]} уже админ.")
            return
        admins.append(uid)
        save_admins(admins)
        bot.reply_to(message, f"✅ {parts[1]} добавлен как админ!")
    except:
        bot.reply_to(message, "❌ Пользователь не найден. Попросите его написать боту.")

@bot.message_handler(commands=['vremove_admin'])
def vremove_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].startswith('@'):
        bot.reply_to(message, "❌ `/vremove_admin @username`", parse_mode="Markdown")
        return
    
    try:
        user = bot.get_chat(parts[1])
        uid = user.id
        admins = load_admins()
        if uid not in admins:
            bot.reply_to(message, f"⚠️ {parts[1]} не админ.")
            return
        admins.remove(uid)
        save_admins(admins)
        bot.reply_to(message, f"✅ {parts[1]} удалён.")
    except:
        bot.reply_to(message, "❌ Пользователь не найден.")

@bot.message_handler(commands=['vadmins_list'])
def vadmins_list(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    admins = load_admins()
    text = "👥 *СПИСОК АДМИНОВ*\n\n"
    text += f"👑 *Владелец:* `{OWNER_ID}`\n\n"
    
    if not admins:
        text += "📭 Админов нет."
    else:
        text += "🛡️ *Админы:*\n"
        for i, uid in enumerate(admins, 1):
            try:
                user = bot.get_chat(uid)
                name = user.username or user.first_name or f"ID:{uid}"
                text += f"{i}. @{name}\n"
            except:
                text += f"{i}. `{uid}`\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ============================================================
# ПОДАРКИ
# ============================================================

def get_gift_emoji(rating):
    """Возвращает эмодзи по рейтингу"""
    r = int(rating)
    if 98 <= r <= 100:
        return "🟣"  # миф
    elif 87 <= r <= 90:
        return "🔵"  # лега
    elif 79 <= r <= 80:
        return "🟢"  # эпик
    else:
        return "⚪"

@bot.message_handler(commands=['vadd_card'])
def vadd_card(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используйте: `/vadd_card 92 \"Название карты\"`", parse_mode="Markdown")
        return
    
    try:
        rating = int(parts[1])
        if rating < 1 or rating > 100:
            bot.reply_to(message, "❌ Рейтинг от 1 до 100")
            return
    except:
        bot.reply_to(message, "❌ Рейтинг должен быть числом")
        return
    
    name = parts[2].strip('"').strip()
    
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    # Проверяем дубликат
    for g in gifts:
        if g["name"].lower() == name.lower():
            bot.reply_to(message, f"⚠️ Карта с таким названием уже есть.")
            return
    
    gifts.append({"rating": rating, "name": name})
    gifts.sort(key=lambda x: x["rating"], reverse=True)
    data["gifts"] = gifts
    save_json(ANICARD_FILE, data)
    
    emoji = get_gift_emoji(rating)
    bot.reply_to(message, f"✅ Добавлено: {emoji} {rating} — {name}")

@bot.message_handler(commands=['vadd_card_remove'])
def vadd_card_remove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ `/vadd_card_remove 92`", parse_mode="Markdown")
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

@bot.message_handler(commands=['vadd_stars'])
def vadd_stars(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используйте: `/vadd_stars 1 100` (место и звёзды)", parse_mode="Markdown")
        return
    
    try:
        place = int(parts[1])
        stars = int(parts[2])
    except:
        bot.reply_to(message, "❌ Введите числа")
        return
    
    if place < 1:
        bot.reply_to(message, "❌ Место >= 1")
        return
    if stars < 15:
        bot.reply_to(message, "❌ Минимум 15 звёзд")
        return
    
    data = load_json(STARS_FILE)
    gifts = data.get("gifts", [])
    
    # Обновляем или добавляем
    found = False
    for g in gifts:
        if g["place"] == place:
            g["stars"] = stars
            found = True
            break
    
    if not found:
        gifts.append({"place": place, "stars": stars})
    
    gifts.sort(key=lambda x: x["stars"], reverse=True)
    data["gifts"] = gifts
    save_json(STARS_FILE, data)
    
    bot.reply_to(message, f"✅ Место {place} → {stars} ⭐")

@bot.message_handler(commands=['vadd_stars_remove'])
def vadd_stars_remove(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец.")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ `/vadd_stars_remove 1`", parse_mode="Markdown")
        return
    
    try:
        place = int(parts[1])
    except:
        bot.reply_to(message, "❌ Введите число")
        return
    
    data = load_json(STARS_FILE)
    gifts = data.get("gifts", [])
    
    found = False
    new_gifts = [g for g in gifts if g["place"] != place]
    if len(new_gifts) == len(gifts):
        bot.reply_to(message, f"⚠️ Место {place} не найдено.")
        return
    
    data["gifts"] = new_gifts
    save_json(STARS_FILE, data)
    bot.reply_to(message, f"✅ Место {place} удалено.")

@bot.message_handler(commands=['vanicard'])
def vanicard(message):
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    if not gifts:
        bot.reply_to(message, "📭 *Список AniCard пуст*", parse_mode="Markdown")
        return
    
    text = "🎁 *ПОДАРКИ ANICARD*\n\n"
    text += "🟣 миф (98-100)\n🔵 лега (87-90)\n🟢 эпик (79-80)\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for g in gifts:
        emoji = get_gift_emoji(g["rating"])
        text += f"{emoji} *{g['rating']}* — {g['name']}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['vstars'])
def vstars(message):
    data = load_json(STARS_FILE)
    gifts = data.get("gifts", [])
    
    if not gifts:
        bot.reply_to(message, "📭 *Список Telegram-звёзд пуст*", parse_mode="Markdown")
        return
    
    text = "⭐ *ПОДАРКИ TELEGRAM (звёзды)*\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for g in gifts:
        text += f"🏆 Место {g['place']} → ⭐ {g['stars']} звёзд\n"
    
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
    if not is_owner(message.from_user.id):
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
print(f"👑 Владелец: {OWNER_ID}")
print("=" * 40)
bot.infinity_polling()
