import telebot
from telebot import types
import json
import os
from datetime import datetime

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8813006955:AAHYH-WEmw5E8Z9h9ZPGhHSHMR-yAnz2yoM"

# ТВОЙ ID (главный админ)
OWNER_ID = 7080227092

DATA_FILE = "scores.json"
QUESTIONS_FILE = "questions_count.json"
ADMINS_FILE = "admins.json"
# =====================

bot = telebot.TeleBot(BOT_TOKEN)

# ===== РАБОТА С АДМИНАМИ =====
def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("admins", [])
    return []

def save_admins(admins):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({"admins": admins}, f, indent=2, ensure_ascii=False)

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in load_admins()

def is_owner_or_admin(message):
    user_id = message.from_user.id
    return is_owner(user_id) or is_admin(user_id)

# ===== КОМАНДА /add_admin_id (ДОБАВЛЯЕТ ПО ID) =====
@bot.message_handler(commands=['add_admin_id'])
def add_admin_by_id(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может добавлять админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/add_admin_id 123456789`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
        
        if user_id == OWNER_ID:
            bot.reply_to(message, "👑 Владелец уже имеет все права!")
            return
        
        admins = load_admins()
        if user_id in admins:
            bot.reply_to(message, f"⚠️ Пользователь с ID {user_id} уже является админом.")
            return
        
        admins.append(user_id)
        save_admins(admins)
        bot.reply_to(message, f"✅ Пользователь с ID `{user_id}` добавлен в админы!", parse_mode="Markdown")
        
    except ValueError:
        bot.reply_to(message, "❌ Введите корректный ID (только цифры)")

# ===== КОМАНДА /remove_admin_id (УДАЛЯЕТ ПО ID) =====
@bot.message_handler(commands=['remove_admin_id'])
def remove_admin_by_id(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может удалять админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/remove_admin_id 123456789`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
        
        admins = load_admins()
        if user_id not in admins:
            bot.reply_to(message, f"⚠️ Пользователь с ID {user_id} не является админом.")
            return
        
        admins.remove(user_id)
        save_admins(admins)
        bot.reply_to(message, f"✅ Пользователь с ID `{user_id}` удалён из админов!", parse_mode="Markdown")
        
    except ValueError:
        bot.reply_to(message, "❌ Введите корректный ID (только цифры)")

# ===== КОМАНДА /admins_list (СПИСОК АДМИНОВ) =====
@bot.message_handler(commands=['admins_list'])
def admins_list(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    admins = load_admins()
    if not admins:
        bot.reply_to(message, "👥 Список админов пуст.")
        return

    text = "👥 *Список админов:*\n\n"
    for i, admin_id in enumerate(admins, 1):
        try:
            user = bot.get_chat(admin_id)
            username = user.username or f"ID: {admin_id}"
            text += f"{i}. @{username} (ID: `{admin_id}`)\n"
        except:
            text += f"{i}. ID: `{admin_id}`\n"
    
    text += f"\n👑 Владелец: `{OWNER_ID}`"

    bot.reply_to(message, text, parse_mode="Markdown")

# ===== ОСТАЛЬНЫЕ ФУНКЦИИ =====
def load_scores():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

def load_questions_count():
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("count", 0)
    return 0

def save_questions_count(count):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f, indent=2, ensure_ascii=False)

def reset_questions_count():
    save_questions_count(0)

scores = load_scores()

# ---------- КОМАНДЫ ----------

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_add = types.KeyboardButton("➕ Добавить баллы")
    btn_top = types.KeyboardButton("🏆 Таблица лидеров")
    btn_question = types.KeyboardButton("❓ Новый вопрос")
    btn_reset = types.KeyboardButton("🔄 Обнулить таблицу")
    btn_save = types.KeyboardButton("💾 Сохранить сезон")
    btn_delete = types.KeyboardButton("❌ Удалить пользователя")
    btn_help = types.KeyboardButton("📖 Помощь")
    btn_admins = types.KeyboardButton("👥 Управление админами")
    markup.add(btn_add, btn_top, btn_question, btn_reset, btn_save, btn_delete, btn_help, btn_admins)

    bot.reply_to(
        message,
        "🤖 *Добро пожаловать в викторину канала ANIARK!*\n\n"
        "📌 *Как это работает:*\n"
        "1️⃣ Ведущий публикует вопрос в канале\n"
        "2️⃣ Участники отвечают в комментариях\n"
        "3️⃣ Админ **отвечает на сообщение** участника и пишет `/add`\n\n"
        "📊 *Команды:*\n"
        "`/add @user [N]` — начислить баллы\n"
        "`/question` — увеличить счётчик вопросов (+1)\n"
        "`/questions_remove N` — убрать N вопросов\n"
        "`/questions_set N` — установить точное количество вопросов\n"
        "`/add_admin_id 123456789` — добавить админа по ID (только владелец)\n"
        "`/remove_admin_id 123456789` — удалить админа по ID (только владелец)\n"
        "`/admins_list` — список админов\n"
        "`/top` — таблица лидеров\n"
        "`/reset` — обнулить всё (только владелец)\n"
        "`/save` — сохранить сезон\n\n"
        "💡 *Как узнать свой ID:* напишите @userinfobot\n\n"
        "Удачи в викторине! 🍀",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== КОМАНДА /add (без счётчика вопросов) =====
@bot.message_handler(commands=['add'])
def add_score(message):
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
        bot.reply_to(message, "❌ Не найден пользователь!\nУкажите @username или ответьте на сообщение участника.")
        return

    for part in parts:
        try:
            num = int(part)
            if num > 0:
                points = num
                break
        except ValueError:
            continue

    scores[username] = scores.get(username, 0) + points
    save_scores(scores)

    word = "балл" if points == 1 else "балла" if points in [2,3,4] else "баллов"
    bot.reply_to(message, f"✅ {username} +{points} {word}! Всего: {scores[username]}")

# ===== КОМАНДА /question =====
@bot.message_handler(commands=['question'])
def add_question(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    new_count = load_questions_count() + 1
    save_questions_count(new_count)
    bot.reply_to(message, f"❓ Новый вопрос засчитан!\n📊 Всего вопросов: *{new_count}*", parse_mode="Markdown")

# ===== КОМАНДА /questions_remove =====
@bot.message_handler(commands=['questions_remove'])
def remove_questions(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/questions_remove N`\nНапример: `/questions_remove 3`", parse_mode="Markdown")
        return

    try:
        n = int(parts[1])
        if n <= 0:
            bot.reply_to(message, "❌ Число должно быть больше 0")
            return
    except ValueError:
        bot.reply_to(message, "❌ Введите число")
        return

    current = load_questions_count()
    new_count = max(0, current - n)
    save_questions_count(new_count)
    bot.reply_to(message, f"➖ Убрано {n} вопросов.\n📊 Всего вопросов: *{new_count}*", parse_mode="Markdown")

# ===== КОМАНДА /questions_set =====
@bot.message_handler(commands=['questions_set'])
def set_questions(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/questions_set N`\nНапример: `/questions_set 10`", parse_mode="Markdown")
        return

    try:
        n = int(parts[1])
        if n < 0:
            bot.reply_to(message, "❌ Число не может быть отрицательным")
            return
    except ValueError:
        bot.reply_to(message, "❌ Введите число")
        return

    save_questions_count(n)
    bot.reply_to(message, f"✅ Количество вопросов установлено: *{n}*", parse_mode="Markdown")

# ===== КОМАНДА /remove (отнять баллы) =====
@bot.message_handler(commands=['remove'])
def remove_score(message):
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
        bot.reply_to(message, "❌ Не найден пользователь!\nУкажите @username или ответьте на сообщение участника.")
        return

    for part in parts:
        try:
            num = int(part)
            if num > 0:
                points = num
                break
        except ValueError:
            continue

    if username not in scores:
        bot.reply_to(message, f"❌ У {username} нет баллов")
        return

    scores[username] = max(0, scores[username] - points)
    save_scores(scores)
    bot.reply_to(message, f"➖ {username} -{points} баллов. Осталось: {scores[username]}")

# ===== КОМАНДА /delete =====
@bot.message_handler(commands=['delete'])
def delete_user(message):
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
        bot.reply_to(message, "❌ Не найден пользователь!\nУкажите @username или ответьте на сообщение участника.")
        return

    if username not in scores:
        bot.reply_to(message, f"❌ Пользователь {username} не найден в таблице.")
        return

    del scores[username]
    save_scores(scores)
    bot.reply_to(message, f"🗑️ Пользователь {username} удалён из таблицы!")

# ===== КОМАНДА /top =====
@bot.message_handler(commands=['top'])
def show_top(message):
    filtered_scores = {k: v for k, v in scores.items() if v > 0}

    if not filtered_scores:
        bot.reply_to(message, "📭 *Таблица пока пуста!*\nСтаньте первым участником! 🏆", parse_mode="Markdown")
        return

    sorted_users = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)
    max_score = max(filtered_scores.values()) if filtered_scores else 0
    questions_count = load_questions_count()

    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ ВИКТОРИНЫ*\n"
    text += f"📊 Всего вопросов: {questions_count}\n"
    text += f"📊 Всего участников: {len(filtered_scores)}\n\n"

    for i, (user, score) in enumerate(sorted_users, 1):
        if i == 1:
            medal = "🥇"
            bonus = "👑"
        elif i == 2:
            medal = "🥈"
            bonus = ""
        elif i == 3:
            medal = "🥉"
            bonus = ""
        else:
            medal = f"{i}."
            bonus = ""

        bar_length = 12
        filled = int((score / max_score) * bar_length) if max_score > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        text += f"{medal} *{user}* {bonus} - {score}\n\n"

    bot.reply_to(message, text, parse_mode="Markdown")

# ===== КОМАНДА /reset (ТОЛЬКО ВЛАДЕЛЕЦ!) =====
@bot.message_handler(commands=['reset'])
def reset_scores(message):
    global scores
    
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может обнулить таблицу!")
        return

    if not scores and load_questions_count() == 0:
        bot.reply_to(message, "📭 Таблица и так пуста. Нечего удалять.")
        return

    scores = {}
    save_scores(scores)
    reset_questions_count()
    bot.reply_to(message, "🗑️ Таблица и счётчик вопросов обнулены владельцем!")

# ===== КОМАНДА /save =====
@bot.message_handler(commands=['save'])
def save_season(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    data = {
        "scores": scores,
        "questions_count": load_questions_count()
    }
    filename = f"season_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    bot.reply_to(message, f"✅ Текущий сезон сохранён в {filename}")

# ===== КОМАНДА /help =====
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "**Для всех:**\n"
        "`/start` — Главное меню\n"
        "`/top` — Таблица лидеров\n\n"
        "**Для админов:**\n"
        "`/add @user [N]` — начислить баллы\n"
        "`/remove @user [N]` — отнять баллы\n"
        "`/delete @user` — удалить пользователя\n"
        "`/question` — новый вопрос (+1)\n"
        "`/questions_remove N` — убрать N вопросов\n"
        "`/questions_set N` — установить точное количество\n"
        "`/save` — сохранить сезон\n\n"
        "**Только для владельца:**\n"
        "`/reset` — обнулить всё\n"
        "`/add_admin_id 123456789` — добавить админа по ID\n"
        "`/remove_admin_id 123456789` — удалить админа по ID\n"
        "`/admins_list` — список админов\n\n"
        "💡 *Как узнать ID:* напишите @userinfobot"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# ---------- ОБРАБОТЧИК КНОПОК ----------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "➕ Добавить баллы":
        bot.reply_to(message, "📝 Ответьте на сообщение участника и напишите `/add`\nИли напишите: `/add @username [количество]`", parse_mode="Markdown")
    elif message.text == "🏆 Таблица лидеров":
        show_top(message)
    elif message.text == "❓ Новый вопрос":
        add_question(message)
    elif message.text == "🔄 Обнулить таблицу":
        reset_scores(message)
    elif message.text == "💾 Сохранить сезон":
        save_season(message)
    elif message.text == "❌ Удалить пользователя":
        bot.reply_to(message, "📝 Напишите: `/delete @username`\nИли ответьте на сообщение участника и напишите `/delete`", parse_mode="Markdown")
    elif message.text == "📖 Помощь":
        help_command(message)
    elif message.text == "👥 Управление админами":
        admins_list(message)

# ---------- ЗАПУСК ----------
print("✅ Бот запущен!")
print(f"👑 Владелец: {OWNER_ID}")
print(f"👥 Админов: {len(load_admins())}")
print("=" * 40)
bot.infinity_polling()
