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
NICKS_FILE = "nicks.json"  # НОВЫЙ ФАЙЛ ДЛЯ ХРАНЕНИЯ КЛИЧЕК
# =====================

bot = telebot.TeleBot(BOT_TOKEN)

# ===== ПРОВЕРКА ФАЙЛОВ =====
def ensure_files_exist():
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump({"admins": []}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({"count": 0}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(NICKS_FILE):
        with open(NICKS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)

ensure_files_exist()

# ===== РАБОТА С КЛИЧКАМИ =====
def load_nicks():
    if os.path.exists(NICKS_FILE):
        with open(NICKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_nicks(nicks):
    with open(NICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(nicks, f, indent=2, ensure_ascii=False)

def get_display_name(username):
    """Возвращает кличку, если есть, или имя без @"""
    nicks = load_nicks()
    clean_name = username.lower().replace('@', '')
    if clean_name in nicks:
        return nicks[clean_name]
    return clean_name

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

# ===== СЛОВАРЬ ДЛЯ ХРАНЕНИЯ СОСТОЯНИЙ ПОДТВЕРЖДЕНИЯ =====
waiting_for_confirmation = {}

# ===== КОМАНДА /nick (установить кличку) =====
@bot.message_handler(commands=['nick'])
def set_nick(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(
            message,
            "❌ Используйте: `/nick @username НоваяКличка`\n"
            "Например: `/nick @ivan Космонавт`",
            parse_mode="Markdown"
        )
        return

    username = parts[1].lower()
    if not username.startswith('@'):
        bot.reply_to(message, "❌ Укажите @username")
        return

    # Убираем @ для поиска
    clean_username = username.replace('@', '')
    
    # Проверяем, есть ли такой пользователь в таблице
    if clean_username not in scores and f"@{clean_username}" not in scores:
        # Проверяем с @
        if clean_username not in scores:
            bot.reply_to(message, f"❌ Пользователь {username} не найден в таблице.")
            return

    new_nick = " ".join(parts[2:])
    
    nicks = load_nicks()
    nicks[clean_username] = new_nick
    save_nicks(nicks)
    
    bot.reply_to(message, f"✅ Пользователю {username} присвоена кличка: *{new_nick}*", parse_mode="Markdown")

# ===== КОМАНДА /nick_remove (удалить кличку) =====
@bot.message_handler(commands=['nick_remove'])
def remove_nick(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/nick_remove @username`\nНапример: `/nick_remove @ivan`", parse_mode="Markdown")
        return

    username = parts[1].lower()
    if not username.startswith('@'):
        bot.reply_to(message, "❌ Укажите @username")
        return

    clean_username = username.replace('@', '')
    
    nicks = load_nicks()
    if clean_username not in nicks:
        bot.reply_to(message, f"⚠️ У пользователя {username} нет клички.")
        return

    del nicks[clean_username]
    save_nicks(nicks)
    bot.reply_to(message, f"✅ Кличка пользователя {username} удалена.")

# ===== КОМАНДА /add_admin_id =====
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

# ===== КОМАНДА /remove_admin_id =====
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

# ===== КОМАНДА /admins_list =====
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
            display_name = get_display_name(username)
            text += f"{i}. {display_name}\n"
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
        "`/nick @user Кличка` — дать участнику кличку\n"
        "`/nick_remove @user` — удалить кличку\n"
        "`/question` — увеличить счётчик вопросов (+1)\n"
        "`/questions_remove N` — убрать N вопросов\n"
        "`/questions_set N` — установить точное количество вопросов\n"
        "`/add_admin_id 123456789` — добавить админа по ID (только владелец)\n"
        "`/remove_admin_id 123456789` — удалить админа по ID (только владелец)\n"
        "`/admins_list` — список админов\n"
        "`/top` — таблица лидеров\n"
        "`/reset` — обнулить всё (только владелец, с подтверждением)\n"
        "`/save` — сохранить сезон\n\n"
        "💡 *Как узнать свой ID:* напишите @userinfobot\n\n"
        "Удачи в викторине! 🍀",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== КОМАНДА /add =====
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

    # Сохраняем в чистом виде (без @)
    clean_username = username.replace('@', '')
    scores[clean_username] = scores.get(clean_username, 0) + points
    save_scores(scores)

    word = "балл" if points == 1 else "балла" if points in [2,3,4] else "баллов"
    display_name = get_display_name(clean_username)
    bot.reply_to(message, f"✅ {display_name} +{points} {word}! Всего: {scores[clean_username]}")

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

# ===== КОМАНДА /remove =====
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

    clean_username = username.replace('@', '')
    
    for part in parts:
        try:
            num = int(part)
            if num > 0:
                points = num
                break
        except ValueError:
            continue

    if clean_username not in scores:
        bot.reply_to(message, f"❌ У {username} нет баллов")
        return

    scores[clean_username] = max(0, scores[clean_username] - points)
    save_scores(scores)
    display_name = get_display_name(clean_username)
    bot.reply_to(message, f"➖ {display_name} -{points} баллов. Осталось: {scores[clean_username]}")

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

    clean_username = username.replace('@', '')

    if clean_username not in scores:
        bot.reply_to(message, f"❌ Пользователь {username} не найден в таблице.")
        return

    del scores[clean_username]
    save_scores(scores)
    
    # Удаляем и кличку, если она есть
    nicks = load_nicks()
    if clean_username in nicks:
        del nicks[clean_username]
        save_nicks(nicks)
    
    bot.reply_to(message, f"🗑️ Пользователь {username} удалён из таблицы!")

# ===== КОМАНДА /top (без тегов, с кличками) =====
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
        display_name = get_display_name(user)
        
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

        text += f"{medal} *{display_name}* {bonus} - {score}\n\n"

    bot.reply_to(message, text, parse_mode="Markdown")

# ===== КОМАНДА /reset (С ПОДТВЕРЖДЕНИЕМ!) =====
@bot.message_handler(commands=['reset'])
def reset_scores(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может обнулить таблицу!")
        return

    if not scores and load_questions_count() == 0:
        bot.reply_to(message, "📭 Таблица и так пуста. Нечего удалять.")
        return

    waiting_for_confirmation[message.chat.id] = True

    bot.reply_to(
        message,
        "⚠️ *ВНИМАНИЕ!*\n\n"
        "Вы собираетесь полностью удалить ТАБЛИЦУ ЛИДЕРОВ и СЧЁТЧИК ВОПРОСОВ.\n"
        "Это действие нельзя отменить!\n\n"
        f"📊 Будет удалено:\n"
        f"• {len(scores)} участников\n"
        f"• {load_questions_count()} вопросов\n\n"
        "Для подтверждения напишите: `ДА`\n"
        "Для отмены напишите что угодно другое.",
        parse_mode="Markdown"
    )

# ===== ОБРАБОТЧИК ПОДТВЕРЖДЕНИЯ =====
@bot.message_handler(func=lambda message: message.chat.id in waiting_for_confirmation)
def confirm_reset(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может обнулить таблицу!")
        return

    waiting_for_confirmation.pop(message.chat.id, None)

    if message.text.strip().upper() == "ДА":
        global scores
        scores = {}
        save_scores(scores)
        reset_questions_count()
        # Очищаем клички при обнулении
        save_nicks({})
        bot.reply_to(message, "🗑️ Таблица, счётчик вопросов и клички обнулены владельцем!")
    else:
        bot.reply_to(message, "❌ Удаление отменено. Таблица сохранена.")

# ===== КОМАНДА /save =====
@bot.message_handler(commands=['save'])
def save_season(message):
    if not is_owner_or_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return

    data = {
        "scores": scores,
        "questions_count": load_questions_count(),
        "nicks": load_nicks()
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
        "`/nick @user Кличка` — дать участнику кличку\n"
        "`/nick_remove @user` — удалить кличку\n"
        "`/remove @user [N]` — отнять баллы\n"
        "`/delete @user` — удалить пользователя\n"
        "`/question` — новый вопрос (+1)\n"
        "`/questions_remove N` — убрать N вопросов\n"
        "`/questions_set N` — установить точное количество\n"
        "`/save` — сохранить сезон\n\n"
        "**Только для владельца:**\n"
        "`/reset` — обнулить всё (с подтверждением)\n"
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
