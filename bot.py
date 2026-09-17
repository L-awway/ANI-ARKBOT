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
DOB_LIMITS_FILE = "dob_limits.json"  # НОВЫЙ ФАЙЛ: доп. вопросы
ANICARD_FILE = "anibattle_gifts.json"
BANS_FILE = "bans.json"
USERNAMES_FILE = "usernames_cache.json"
DOB_HISTORY_FILE = "dob_history.json"
DELETED_FILE = "deleted_users.json"
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
        (DOB_LIMITS_FILE, {}),  # НОВЫЙ ФАЙЛ
        (ANICARD_FILE, {"gifts": []}),
        (BANS_FILE, {"banned": []}),
        (USERNAMES_FILE, {}),
        (DOB_HISTORY_FILE, {}),
        (DELETED_FILE, {}),
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

# ===== ЛИМИТЫ (5 ответов в день) =====
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

def reset_limit(username):
    clean = username.lower().replace('@', '')
    limits = load_json(LIMITS_FILE)
    if clean in limits:
        del limits[clean]
        save_json(LIMITS_FILE, limits)

# ===== ДОПОЛНИТЕЛЬНЫЕ ЛИМИТЫ (общие на день) =====
def check_dob_limit(kind):
    """
    kind = 1 или 2.
    Возвращает (можно_ли, осталось).
    """
    today = get_msk_date()
    limits = load_json(DOB_LIMITS_FILE)
    max_count = 8 if kind == 1 else 2
    
    today_data = limits.get(today, {})
    count = today_data.get(f"vdob{kind}", 0)
    
    if count >= max_count:
        return False, 0
    return True, max_count - count

def add_dob_limit(kind):
    today = get_msk_date()
    limits = load_json(DOB_LIMITS_FILE)
    
    if today not in limits:
        limits[today] = {"vdob1": 0, "vdob2": 0}
    
    key = f"vdob{kind}"
    limits[today][key] = limits[today].get(key, 0) + 1
    save_json(DOB_LIMITS_FILE, limits)

def remove_dob_limit(kind):
    """Уменьшает счётчик на 1 (при откате)."""
    today = get_msk_date()
    limits = load_json(DOB_LIMITS_FILE)
    
    if today not in limits:
        return
    
    key = f"vdob{kind}"
    if key in limits[today] and limits[today][key] > 0:
        limits[today][key] -= 1
        save_json(DOB_LIMITS_FILE, limits)

def reset_dob_limit():
    """Сбрасывает все счётчики доп. вопросов за сегодня."""
    today = get_msk_date()
    limits = load_json(DOB_LIMITS_FILE)
    if today in limits:
        del limits[today]
        save_json(DOB_LIMITS_FILE, limits)

# ===== ИСТОРИЯ ДОП. ВОПРОСОВ (для отката) =====
def add_dob_history(username, kind, points):
    today = get_msk_date()
    history = load_json(DOB_HISTORY_FILE)
    
    if today not in history:
        history[today] = []
    
    now = datetime.now(timezone(timedelta(hours=3))).strftime("%H:%M:%S")
    history[today].append({
        "user": username.lower().replace('@', ''),
        "kind": kind,
        "points": points,
        "time": now
    })
    save_json(DOB_HISTORY_FILE, history)

def get_last_dob_for_user(username, kind=None):
    """
    Возвращает последнее начисление для пользователя.
    Если kind задан (1 или 2), ищет только этого типа.
    Возвращает индекс в списке или None.
    """
    today = get_msk_date()
    history = load_json(DOB_HISTORY_FILE)
    clean = username.lower().replace('@', '')
    
    if today not in history:
        return None
    
    entries = history[today]
    for i in range(len(entries) - 1, -1, -1):
        e = entries[i]
        if e["user"] == clean:
            if kind is None or e["kind"] == kind:
                return i
    return None

def pop_dob_history(index):
    """Удаляет запись из истории по индексу и возвращает её."""
    today = get_msk_date()
    history = load_json(DOB_HISTORY_FILE)
    
    if today not in history:
        return None
    
    entries = history[today]
    if index < 0 or index >= len(entries):
        return None
    
    entry = entries.pop(index)
    history[today] = entries
    save_json(DOB_HISTORY_FILE, history)
    return entry

def reset_dob_history():
    today = get_msk_date()
    history = load_json(DOB_HISTORY_FILE)
    if today in history:
        del history[today]
        save_json(DOB_HISTORY_FILE, history)
# ===== БАНЫ =====
def is_banned(username):
    clean = username.lower().replace('@', '')
    bans = load_json(BANS_FILE).get("banned", [])
    return clean in [b.lower() for b in bans]

def ban_user(username):
    clean = username.lower().replace('@', '')
    bans = load_json(BANS_FILE)
    if clean not in [b.lower() for b in bans.get("banned", [])]:
        bans.setdefault("banned", []).append(clean)
        save_json(BANS_FILE, bans)

def unban_user(username):
    clean = username.lower().replace('@', '')
    bans = load_json(BANS_FILE)
    banned = bans.get("banned", [])
    new_banned = [b for b in banned if b.lower() != clean]
    bans["banned"] = new_banned
    save_json(BANS_FILE, bans)

# ===== КЭШ USERNAME -> ID =====
def load_usernames_cache():
    return load_json(USERNAMES_FILE)

def save_usernames_cache(cache):
    save_json(USERNAMES_FILE, cache)

def remember_user(user):
    if user.username:
        cache = load_usernames_cache()
        cache[user.username.lower()] = user.id
        save_usernames_cache(cache)

def get_user_id_by_username(username):
    cache = load_usernames_cache()
    return cache.get(username.lower())

def forget_user(username):
    """Удаляет пользователя из кэша username -> ID."""
    clean = username.lower().replace('@', '')
    cache = load_usernames_cache()
    if clean in cache:
        del cache[clean]
        save_usernames_cache(cache)

# ===== СПИСОК УДАЛЁННЫХ (защита от воскрешения) =====
def load_deleted():
    return load_json(DELETED_FILE)

def save_deleted(data):
    save_json(DELETED_FILE, data)

def mark_deleted(username, user_id=None):
    clean = username.lower().replace('@', '')
    data = load_deleted()
    data[clean] = True
    if user_id is not None:
        data[f"id_{user_id}"] = True
    save_deleted(data)

def is_deleted(username, user_id=None):
    clean = username.lower().replace('@', '')
    data = load_deleted()
    if clean in data:
        return True
    if user_id is not None and f"id_{user_id}" in data:
        return True
    return False

def unmark_deleted(username, user_id=None):
    clean = username.lower().replace('@', '')
    data = load_deleted()
    if clean in data:
        del data[clean]
    if user_id is not None and f"id_{user_id}" in data:
        del data[f"id_{user_id}"]
    save_deleted(data)
        
# ===== АДМИНЫ =====
OWNER_USERNAME = "Zhongli_3112"

def load_admins():
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("admins", [])
    except Exception as e:
        print(f"❌ load_admins error: {e}")
        return []

def save_admins(admins):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({"admins": admins}, f, indent=2, ensure_ascii=False)

def is_owner_username(username):
    if not username:
        return False
    return username.lower() == OWNER_USERNAME.lower()

def is_admin_username(username):
    if not username:
        return False
    if is_owner_username(username):
        return True
    admins = load_admins()
    return username.lower() in [a.lower() for a in admins]

def is_owner_or_admin(message):
    username = message.from_user.username
    return is_owner_username(username) or is_admin_username(username)

# ===== КЛИЧКИ =====
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
# ОПРЕДЕЛЕНИЕ ЦЕЛИ
# ============================================================

def get_bot_username():
    try:
        return bot.get_me().username.lower()
    except:
        return "aniark_viktorins_bot"

def extract_points(message):
    """Ищет число в тексте команды. По умолчанию 1."""
    parts = message.text.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    return 1
    
def get_target_user(message):
    """
    Возвращает (user_id, user_name, username, from_reply):
    - user_id: int или None
    - user_name: str
    - username: str (без @)
    - from_reply: True если это свайп, False если @username
    """
    text_parts = message.text.split()
    bot_username = get_bot_username()

    # 1. @username в тексте
    for part in text_parts:
        if part.startswith('@') and len(part) > 1:
            username = part[1:].lower()
            if username == bot_username:
                continue
            user_id = get_user_id_by_username(username)
            name = get_display_name(username)
            return user_id, name, username, False

    # 2. Свайп
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        username = (user.username or f"user_{user.id}").lower()
        name = get_display_name(username)
        return user.id, name, username, True

    return None, None, None, False

# ============================================================
# КОМАНДЫ
# ============================================================

@bot.message_handler(commands=['vstart'])
def vstart(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🏆 Таблица"),
        types.KeyboardButton("🎁 Подарки"),
        types.KeyboardButton("🧑‍💻💼 Админы"),
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
        "`/vnick @user Кличка` — дать кличку\n"
        "`/vdob1 @user` — доп. вопрос (+1 балл, 8/день)\n"
        "`/vdob2 @user` — доп. вопрос (+2 балла, 2/день)\n\n"
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
        "`/vgifts` — подарки\n"
        "`/vanicard` — список AniCard\n"
        "`/vstars` — список Telegram-звёзд\n\n"
        "*Для админов:*\n"
        "`/vadd @user [N]` — баллы (лимит 5/день)\n"
        "`/vdob1 @user` — доп. +1 балл (лимит 8/день)\n"
        "`/vdob2 @user` — доп. +2 балла (лимит 2/день)\n"
        "`/vremove @user [N]` — отнять\n"
        "`/vdelete @user` — удалить\n"
        "`/vrestore @user` — восстановить удалённого\n"
        "`/vnick @user Кличка` — кличка\n"
        "`/vnick_remove @user` — убрать кличку\n"
        "`/vban @user` — забанить\n"
        "`/vunban @user` — разбанить\n"
        "`/vquestions_add N` — добавить N вопросов\n"
        "`/vquestions_remove N` — убрать N вопросов\n"
        "`/vquestions_set N` — установить количество вопросов\n"
        "`/vdob_rollback @user [1|2]` — откатить доп. вопрос\n"
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
    scores = load_scores()
    nicks = load_nicks()
    deleted = load_deleted()
    
    if not scores:
        bot.reply_to(message, "📭 Таблица лидеров пуста.")
        return
    
    # Фильтруем удалённых
    filtered_scores = {}
    for username, score in scores.items():
        # Пропускаем, если username в списке удалённых
        if username in deleted:
            continue
        # Пропускаем, если для этого username есть id_* в удалённых
        # (необязательно, но полезно)
        filtered_scores[username] = score
    
    if not filtered_scores:
        bot.reply_to(message, "📭 Таблица лидеров пуста.")
        return
    
    sorted_scores = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)
    questions = load_json(QUESTIONS_FILE).get("count", 0)
    
    text = "🏆 ТАБЛИЦА ЛИДЕРОВ\n"
    text += f"❓ Вопросов: {questions}\n"
    text += f"👥 Участников: {len(filtered_scores)}\n\n"
    
    for i, (username, score) in enumerate(sorted_scores[:20], 1):
        display_name = nicks.get(username, username)
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        text += f"{medal} {display_name} — {score}\n"
    
    bot.reply_to(message, text)

# ===== /vadd (С ЛИМИТОМ 5) =====
@bot.message_handler(commands=['vadd', 'add'])
def vadd(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)
    
    target_id, user_name, username, from_reply = get_target_user(message)

    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    if target_id is not None and target_id == message.from_user.id:
        bot.reply_to(message, "❌ Вы не можете начислять баллы самому себе.")
        return

    clean_key = username.lower().replace('@', '')
    
    # === ЗАЩИТА ОТ ВОСКРЕШЕНИЯ ===
    if is_deleted(clean_key, target_id):
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} был удалён из таблицы.\n"
            f"Чтобы вернуть его — используйте `/vrestore @{username}`."
        )
        return
    if not from_reply and clean_key not in scores:
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} не найден в таблице.\n"
            f"Свайпните его сообщение (ответьте) и напишите `/vadd` — тогда он добавится."
        )
        return
    # ==============================

    if is_banned(clean_key):
        bot.reply_to(message, f"❌ @{username} забанен и не может получать баллы.")
        return

    can_add, remaining = check_limit(clean_key)
    if not can_add:
        bot.reply_to(
            message,
            f"❌ {user_name} уже ответил на 5 вопросов сегодня.\n"
            f"Лимит обновится в 00:00 (МСК)."
        )
        return

    points = extract_points(message)

    if clean_key not in scores:
        scores[clean_key] = 0

    scores[clean_key] += points
    save_scores(scores)

    add_limit(clean_key)

    _, remaining_after = check_limit(clean_key)

    warning = ""
    if target_id is None:
        warning = "\n⚠️ ID ещё не известен. Как только человек напишет в чат — привяжется автоматически."

    bot.reply_to(
        message,
        f"✅ {user_name} +{points} балл(ов)! Всего: {scores[clean_key]}\n"
        f"📊 Осталось ответов сегодня: {remaining_after}/5{warning}"
    )

# ===== /vdob1 (+1 БАЛЛ, 8 РАЗ В ДЕНЬ — ОБЩИЙ ЛИМИТ) =====
@bot.message_handler(commands=['vdob1'])
def vdob1(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)

    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    if target_id is not None and target_id == message.from_user.id:
        bot.reply_to(message, "❌ Вы не можете начислять баллы самому себе.")
        return

    clean_key = username.lower().replace('@', '')
    
    # === ЗАЩИТА ОТ ВОСКРЕШЕНИЯ ===
    if is_deleted(clean_key, target_id):
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} был удалён из таблицы.\n"
            f"Чтобы вернуть его — используйте `/vrestore @{username}`."
        )
        return
    if not from_reply and clean_key not in scores:
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} не найден в таблице.\n"
            f"Свайпните его сообщение (ответьте) и напишите `/vdob1` — тогда он добавится."
        )
        return
    # ==============================

    if is_banned(clean_key):
        bot.reply_to(message, f"❌ @{username} забанен и не может получать баллы.")
        return

    # === ПРОВЕРКА ОБЩЕГО ЛИМИТА ===
    can_add, remaining = check_dob_limit(1)
    if not can_add:
        bot.reply_to(
            message,
            f"❌ Дополнительные вопросы (+1 балл) на сегодня исчерпаны (8/8).\n"
            f"Лимит обновится в 00:00 (МСК)."
        )
        return
    # ================================

    if clean_key not in scores:
        scores[clean_key] = 0

    scores[clean_key] += 1
    save_scores(scores)

    add_dob_limit(1)
    add_dob_history(clean_key, 1, 1)

    _, remaining_after = check_dob_limit(1)

    bot.reply_to(
        message,
        f"✅ {user_name} +1 балл (доп. вопрос)!\n"
        f"Всего: {scores[clean_key]}\n"
        f"📊 Осталось доп. вопросов (+1) на сегодня: {remaining_after}/8"
    )

# ===== /vdob2 (+2 БАЛЛА, 2 РАЗА В ДЕНЬ — ОБЩИЙ ЛИМИТ) =====
@bot.message_handler(commands=['vdob2'])
def vdob2(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)

    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    if target_id is not None and target_id == message.from_user.id:
        bot.reply_to(message, "❌ Вы не можете начислять баллы самому себе.")
        return

    clean_key = username.lower().replace('@', '')
    
    # === ЗАЩИТА ОТ ВОСКРЕШЕНИЯ ===
    if is_deleted(clean_key, target_id):
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} был удалён из таблицы.\n"
            f"Чтобы вернуть его — используйте `/vrestore @{username}`."
        )
        return
    if not from_reply and clean_key not in scores:
        bot.reply_to(
            message,
            f"❌ Пользователь @{username} не найден в таблице.\n"
            f"Свайпните его сообщение (ответьте) и напишите `/vdob2` — тогда он добавится."
        )
        return
    # ==============================

    if is_banned(clean_key):
        bot.reply_to(message, f"❌ @{username} забанен и не может получать баллы.")
        return

    # === ПРОВЕРКА ОБЩЕГО ЛИМИТА ===
    can_add, remaining = check_dob_limit(2)
    if not can_add:
        bot.reply_to(
            message,
            f"❌ Дополнительные вопросы (+2 балла) на сегодня исчерпаны (2/2).\n"
            f"Лимит обновится в 00:00 (МСК)."
        )
        return
    # ================================

    if clean_key not in scores:
        scores[clean_key] = 0

    scores[clean_key] += 2
    save_scores(scores)

    add_dob_limit(2)
    add_dob_history(clean_key, 2, 2)

    _, remaining_after = check_dob_limit(2)

    bot.reply_to(
        message,
        f"✅ {user_name} +2 балла (доп. вопрос)!\n"
        f"Всего: {scores[clean_key]}\n"
        f"📊 Осталось доп. вопросов (+2) на сегодня: {remaining_after}/2"
    )

# ===== /vdob_rollback (ОТКАТ ДОП. ВОПРОСА) =====
@bot.message_handler(commands=['vdob_rollback'])
def vdob_rollback(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)

    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    clean_key = username.lower().replace('@', '')

    # Определяем, какой тип откатывать (если указан)
    kind = None
    parts = message.text.split()
    for part in parts:
        if part.isdigit():
            k = int(part)
            if k in (1, 2):
                kind = k
                break

    # Ищем последнее начисление
    idx = get_last_dob_for_user(clean_key, kind)
    if idx is None:
        bot.reply_to(
            message,
            f"❌ У @{username} нет начислений доп. вопросов" + 
            (f" (тип +{kind})" if kind else "") + " за сегодня."
        )
        return

    # Забираем запись из истории
    entry = pop_dob_history(idx)
    if entry is None:
        bot.reply_to(message, "❌ Не удалось найти запись для отката.")
        return

    e_kind = entry["kind"]
    e_points = entry["points"]

    # Уменьшаем баллы у пользователя
    if clean_key in scores:
        scores[clean_key] = max(0, scores[clean_key] - e_points)
        save_scores(scores)

    # Возвращаем попытку в счётчик
    remove_dob_limit(e_kind)

    _, remaining = check_dob_limit(e_kind)

    bot.reply_to(
        message,
        f"↩️ Откат выполнен!\n"
        f"👤 {user_name} — снято {e_points} балл(ов)\n"
        f"📊 Осталось доп. вопросов (+{e_kind}) на сегодня: {remaining}/{8 if e_kind == 1 else 2}"
    )

# ===== /vremove =====
@bot.message_handler(commands=['vremove'])
def vremove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)
    
    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    if target_id is not None and target_id == message.from_user.id:
        bot.reply_to(message, "❌ Вы не можете снимать баллы самому себе.")
        return

    points = extract_points(message)
    clean = username.lower().replace('@', '')
    scores_local = load_scores()
    
    if clean not in scores_local:
        bot.reply_to(message, f"❌ У {user_name} нет баллов.")
        return
    
    scores_local[clean] = max(0, scores_local[clean] - points)
    save_scores(scores_local)
    name = get_display_name(clean)
    
    bot.reply_to(message, f"➖ {name} -{points} баллов. Осталось: {scores_local[clean]}")

# ===== /vdelete (ПОЛНАЯ ОЧИСТКА) =====
@bot.message_handler(commands=['vdelete'])
def vdelete(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)
    
    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    if target_id is not None and target_id == message.from_user.id:
        bot.reply_to(message, "❌ Вы не можете удалить себя из таблицы.")
        return

    clean = username.lower().replace('@', '')
    scores_local = load_scores()
    
    if clean not in scores_local:
        bot.reply_to(message, f"❌ Пользователь {user_name} не найден в таблице.")
        return
    
    # 1. Удаляем из баллов
    del scores_local[clean]
    save_scores(scores_local)
    
    # 2. Удаляем кличку
    nicks = load_nicks()
    if clean in nicks:
        del nicks[clean]
        save_nicks(nicks)
    
    # 3. Сбрасываем лимиты (основные и доп)
    reset_limit(clean)
    # НЕ трогаем общий счётчик, но убираем записи пользователя из истории
    # (не критично, но чисто)
    pass  # Счётчик доп. вопросов — общий, его не сбрасываем
    
    # 4. Убираем из банов (если был)
    unban_user(clean)
    
    # 5. УДАЛЯЕМ ИЗ КЭША USERNAME -> ID (главное!)
    forget_user(clean)
    
    # 5.1. Помечаем как удалённого (защита от воскрешения)
    mark_deleted(clean, target_id)
    
    # 6. Очищаем историю доп. вопросов для пользователя
    today = get_msk_date()
    history = load_json(DOB_HISTORY_FILE)
    if today in history:
        history[today] = [e for e in history[today] if e["user"] != clean]
        save_json(DOB_HISTORY_FILE, history)
    
    bot.reply_to(message, f"🗑️ {user_name} удалён из таблицы (полностью).")

# ===== /vrestore (ВОССТАНОВИТЬ УДАЛЁННОГО) =====
@bot.message_handler(commands=['vrestore'])
def vrestore(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)

    target_id, user_name, username, from_reply = get_target_user(message)

    if username is None:
        bot.reply_to(message, "❌ Укажите @username (не бота) или ответьте (свайпните) на сообщение участника.")
        return

    clean_key = username.lower().replace('@', '')

    if not is_deleted(clean_key, target_id):
        bot.reply_to(message, f"⚠️ Пользователь @{username} не находится в списке удалённых.")
        return

    unmark_deleted(clean_key, target_id)

    bot.reply_to(
        message,
        f"✅ Пользователь @{username} восстановлен.\n"
        f"Теперь можно начислять ему баллы через `/vadd` или `/vdob1` / `/vdob2`."
    )
    
# ===== /vnick =====
@bot.message_handler(commands=['vnick'])
def vnick(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    message.text = ' '.join(parts)
    parts = message.text.split()

    if len(parts) < 3:
        bot.reply_to(message, "❌ Используйте: /vnick @user Кличка")
        return

    username = None
    nick_start_index = None
    bot_username = get_bot_username()
    
    for i, part in enumerate(parts[1:], 1):
        if part.startswith('@') and len(part) > 1:
            uname = part[1:].lower()
            if uname == bot_username:
                continue
            username = uname
            nick_start_index = i + 1
            break
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username (не бота). Пример: /vnick @user Кличка")
        return
    
    if nick_start_index is None or nick_start_index >= len(parts):
        bot.reply_to(message, "❌ Укажите кличку. Пример: /vnick @user Кличка")
        return

    new_nick = ' '.join(parts[nick_start_index:])
    clean_username = username.replace('@', '').lower()
    
    scores_local = load_scores()
    if clean_username not in scores_local:
        bot.reply_to(message, f"❌ Пользователь @{username} не найден в таблице. Сначала начислите ему баллы.")
        return

    nicks = load_nicks()
    nicks[clean_username] = new_nick
    save_nicks(nicks)
    
    bot.reply_to(message, f"✅ Пользователь @{username} переименован в «{new_nick}»")

# ===== /vnick_remove =====
@bot.message_handler(commands=['vnick_remove'])
def vnick_remove(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/vnick_remove @user`", parse_mode="Markdown")
        return
    
    username = parts[1].lower()
    clean = username.replace('@', '')
    
    nicks = load_nicks()
    if clean not in nicks:
        bot.reply_to(message, f"⚠️ У @{username} нет клички.")
        return
    
    del nicks[clean]
    save_nicks(nicks)
    bot.reply_to(message, f"✅ Кличка @{username} удалена.")

# ===== /vban =====
@bot.message_handler(commands=['vban'])
def vban(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
    username = None
    for part in parts:
        if part.startswith('@') and len(part) > 1:
            uname = part[1:].lower()
            if uname != get_bot_username():
                username = uname
                break
    
    if not username and message.reply_to_message:
        user = message.reply_to_message.from_user
        username = (user.username or f"user_{user.id}").lower()
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username (не бота).")
        return
    
    clean = username.replace('@', '').lower()
    
    if is_banned(clean):
        bot.reply_to(message, f"⚠️ @{username} уже забанен.")
        return
    
    ban_user(clean)
    bot.reply_to(message, f"🚫 @{username} забанен.")

# ===== /vunban =====
@bot.message_handler(commands=['vunban'])
def vunban(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
    username = None
    for part in parts:
        if part.startswith('@') and len(part) > 1:
            uname = part[1:].lower()
            if uname != get_bot_username():
                username = uname
                break
    
    if not username and message.reply_to_message:
        user = message.reply_to_message.from_user
        username = (user.username or f"user_{user.id}").lower()
    
    if not username:
        bot.reply_to(message, "❌ Укажите @username (не бота).")
        return
    
    clean = username.replace('@', '').lower()
    
    if not is_banned(clean):
        bot.reply_to(message, f"⚠️ @{username} не забанен.")
        return
    
    unban_user(clean)
    bot.reply_to(message, f"✅ @{username} разбанен.")

# ===== /vquestions_add (ДОБАВИТЬ N ВОПРОСОВ) =====
@bot.message_handler(commands=['vquestions_add'])
def vquestions_add(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()

    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/vquestions_add N`", parse_mode="Markdown")
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
    data["count"] = data.get("count", 0) + n
    save_json(QUESTIONS_FILE, data)
    bot.reply_to(message, f"➕ Добавлено {n}. Всего: *{data['count']}*", parse_mode="Markdown")
    
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

@bot.message_handler(commands=['vadd_admin'])
def vadd_admin(message):
    if not is_owner_username(message.from_user.username):
        bot.reply_to(message, "⛔ Только владелец может добавлять админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
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

@bot.message_handler(commands=['vremove_admin'])
def vremove_admin(message):
    if not is_owner_username(message.from_user.username):
        bot.reply_to(message, "⛔ Только владелец может удалять админов.")
        return
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
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

@bot.message_handler(commands=['vadmins_list'])
def vadmins_list(message):
    admins = load_admins()
    text = "👥 СПИСОК АДМИНОВ\n\n"
    text += f"👑 Владелец: {OWNER_USERNAME}\n\n"
    
    if not admins:
        text += "📭 Добавленных админов нет."
    else:
        text += f"🛡️ Админы ({len(admins)}):\n"
        for i, username in enumerate(admins, 1):
            text += f"{i}. {username}\n"
    
    bot.reply_to(message, text)

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
    
    parts = message.text.split()
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
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
    if '@' in parts[0]:
        parts[0] = parts[0].split('@')[0]
    parts = ' '.join(parts).split()
    
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
    
    gifts_sorted = sorted(gifts, key=lambda x: x["price"], reverse=True)
    text = "🎁 *ПОДАРКИ ANICARD*\n\n"
    
    for i, g in enumerate(gifts_sorted, 1):
        emoji = get_gift_emoji(g["rating"])
        text += f"🏆 *Место {i}* → {emoji} {g['rating']} — {g['name']} — {g['price']} поинтов\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['vstars'])
def vstars(message):
    data = load_json(ANICARD_FILE)
    gifts = data.get("gifts", [])
    
    filtered = [g for g in gifts if g.get("price", 0) >= 15]
    filtered.sort(key=lambda x: x["price"], reverse=True)
    
    if not filtered:
        bot.reply_to(message, "📭 *Список Telegram-звёзд пуст*\n(карт с ценой ≥ 15 нет)", parse_mode="Markdown")
        return
    
    text = "⭐ *ПОДАРКИ TELEGRAM (звёзды)*\n\n"
    
    for i, g in enumerate(filtered, 1):
        text += f"🏆 Место {i} → ⭐ {g['price']} звёзд\n"
    
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
    save_json(DOB_LIMITS_FILE, {})
    save_json(DOB_HISTORY_FILE, {})
    save_json(BANS_FILE, {"banned": []})
    save_json(DELETED_FILE, {})
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
    elif text == "🧑‍💻💼 Админы":
        vadmins_list(message)
    elif text == "📖 Помощь":
        vhelp(message)

# ============================================================
# ЗАПОМИНАНИЕ ID ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

@bot.message_handler(func=lambda message: True, content_types=['text'])
def remember_all_users(message):
    if message.from_user:
        remember_user(message.from_user)

# ============================================================
# ЗАПУСК
# ============================================================

print("✅ Викторина-бот запущен!")
print(f"👑 Владелец: @{OWNER_USERNAME}")
print("=" * 40)
bot.infinity_polling()
