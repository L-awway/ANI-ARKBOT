import telebot
from telebot import types
import json
import os
from datetime import datetime

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8813006955:AAHYH-WEmw5E8Z9h9ZPGhHSHMR-yAnz2yoM"
ADMIN_IDS = [7080227092]
DATA_FILE = "scores.json"
QUESTIONS_FILE = "questions_count.json"
# =====================

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения состояний ожидания подтверждения
waiting_for_confirmation = {}

def is_admin(message):
    return message.from_user.id in ADMIN_IDS

def load_scores():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

# ===== ФУНКЦИИ ДЛЯ СЧЁТЧИКА ВОПРОСОВ =====
def load_questions_count():
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("count", 0)
    return 0

def save_questions_count(count):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f, indent=2, ensure_ascii=False)

def increment_questions():
    count = load_questions_count() + 1
    save_questions_count(count)
    return count

def reset_questions_count():
    save_questions_count(0)
# ==========================================

scores = load_scores()

# ---------- КОМАНДЫ ----------

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_add = types.KeyboardButton("➕ Добавить баллы")
    btn_top = types.KeyboardButton("🏆 Таблица лидеров")
    btn_reset = types.KeyboardButton("🔄 Обнулить таблицу")
    btn_save = types.KeyboardButton("💾 Сохранить сезон")
    btn_delete = types.KeyboardButton("❌ Удалить пользователя")
    btn_help = types.KeyboardButton("📖 Помощь")
    markup.add(btn_add, btn_top, btn_reset, btn_save, btn_delete, btn_help)
    
    bot.reply_to(
        message,
        "🤖 *Добро пожаловать в викторину канала ANIARK!*\n\n"
        "📌 *Как это работает:*\n"
        "1️⃣ Ведущий публикует вопрос в канале\n"
        "2️⃣ Участники отвечают в комментариях\n"
        "3️⃣ Админ **отвечает на сообщение** участника и пишет \n\n"
        "Удачи в викторине! 🍀",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['add'])
def add_score(message):
    if not is_admin(message):
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
            bot.reply_to(message, f"⚠️ У пользователя нет @username. Использую имя: {username}")
    
    if not username:
        bot.reply_to(message, "❌ Не найден пользователь!\n\n📌 *Как правильно:*\n1️⃣ Ответьте на сообщение участника\n2️⃣ Напишите `/add`\n\nИли укажите @username в команде: `/add @ivan 5`", parse_mode="Markdown")
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
    
    new_count = increment_questions()
    
    word = "балл" if points == 1 else "балла" if points in [2,3,4] else "баллов"
    bot.reply_to(message, f"✅ {username} +{points} {word}! Всего: {scores[username]}\n❓ Вопрос #{new_count} засчитан!")

@bot.message_handler(commands=['remove'])
def remove_score(message):
    if not is_admin(message):
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

@bot.message_handler(commands=['delete'])
def delete_user(message):
    if not is_admin(message):
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
        
        text += f"{medal} *{user}* {bonus} - {score}\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

# ===== ОБНОВЛЁННАЯ КОМАНДА /reset С ПОДТВЕРЖДЕНИЕМ =====
@bot.message_handler(commands=['reset'])
def reset_scores(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    # Проверяем, есть ли вообще данные для удаления
    if not scores and load_questions_count() == 0:
        bot.reply_to(message, "📭 Таблица и так пуста. Нечего удалять.")
        return
    
    # Запоминаем, кто запросил удаление
    waiting_for_confirmation[message.chat.id] = True
    
    # Спрашиваем подтверждение
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

# Обработчик для подтверждения удаления
@bot.message_handler(func=lambda message: message.chat.id in waiting_for_confirmation)
def confirm_reset(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔ Доступ только у админов.")
        return
    
    # Удаляем из списка ожидания
    waiting_for_confirmation.pop(message.chat.id, None)
    
    # Проверяем, написал ли пользователь "ДА"
    if message.text.strip().upper() == "ДА":
        global scores
        scores = {}
        save_scores(scores)
        reset_questions_count()
        bot.reply_to(message, "✅ Таблица и счётчик вопросов успешно обнулены!")
    else:
        bot.reply_to(message, "❌ Удаление отменено. Таблица сохранена.")

@bot.message_handler(commands=['save'])
def save_season(message):
    if not is_admin(message):
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

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "`/add` — начислить 1 балл (при ответе на сообщение)\n"
        "`/add 5` — начислить 5 баллов\n"
        "`/add @user 3` — начислить 3 балла @user\n"
        "`/remove @user [N]` — Отнять N баллов\n"
        "`/delete @user` — Удалить пользователя\n"
        "`/top` — Таблица лидеров\n"
        "`/reset` — Обнулить всё (с подтверждением)\n"
        "`/save` — Сохранить сезон\n\n"
        "💡 *Совет:* ответьте на сообщение участника и напишите `/add` — бот сам определит, кому начислить баллы!\n"
        "📌 Каждая команда `/add` автоматически засчитывает новый вопрос!\n\n"
        "📌 *Команды /add, /remove, /delete, /reset, /save доступны ТОЛЬКО админам!*"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# ---------- ОБРАБОТЧИК КНОПОК ----------
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "➕ Добавить баллы":
        bot.reply_to(message, "📝 Ответьте на сообщение участника и напишите `/add`\nИли напишите: `/add @username [количество]`", parse_mode="Markdown")
    elif message.text == "🏆 Таблица лидеров":
        show_top(message)
    elif message.text == "🔄 Обнулить таблицу":
        reset_scores(message)
    elif message.text == "💾 Сохранить сезон":
        save_season(message)
    elif message.text == "❌ Удалить пользователя":
        bot.reply_to(message, "📝 Напишите: `/delete @username`\nИли ответьте на сообщение участника и напишите `/delete`", parse_mode="Markdown")
    elif message.text == "📖 Помощь":
        help_command(message)

# ---------- ЗАПУСК ----------
print("✅ Бот запущен!")
print("📊 Версия с подтверждением удаления таблицы")
print("=" * 40)
bot.infinity_polling()