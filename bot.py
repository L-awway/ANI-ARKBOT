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

# ===== КОМАНДА /add_admin (работает!) =====
@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    # Только владелец может добавлять админов
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может добавлять админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/add_admin @username`\nНапример: `/add_admin @ivan`", parse_mode="Markdown")
        return

    username = parts[1]
    if not username.startswith('@'):
        bot.reply_to(message, "❌ Укажите @username")
        return

    # Пытаемся найти пользователя по username
    try:
        # Делаем запрос к Telegram API, чтобы получить ID пользователя
        user_info = bot.get_chat(username)
        user_id = user_info.id
        
        # Проверяем, не является ли пользователь владельцем
        if user_id == OWNER_ID:
            bot.reply_to(message, "👑 Владелец уже имеет все права!")
            return
        
        # Проверяем, не добавлен ли уже
        admins = load_admins()
        if user_id in admins:
            bot.reply_to(message, f"⚠️ Пользователь {username} уже является админом.")
            return
        
        # Добавляем админа
        admins.append(user_id)
        save_admins(admins)
        bot.reply_to(message, f"✅ Пользователь {username} добавлен в админы!")
        
    except Exception as e:
        bot.reply_to(
            message,
            f"❌ Не удалось найти пользователя {username}.\n\n"
            f"Возможные причины:\n"
            f"1️⃣ У пользователя нет @username\n"
            f"2️⃣ Пользователь ещё не писал боту\n"
            f"3️⃣ Неправильно указан username\n\n"
            f"Попробуйте узнать ID через @userinfobot и добавить вручную в файл `admins.json`",
            parse_mode="Markdown"
        )

# ===== КОМАНДА /remove_admin (работает!) =====
@bot.message_handler(commands=['remove_admin'])
def remove_admin(message):
    # Только владелец может удалять админов
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⛔ Только владелец может удалять админов.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: `/remove_admin @username`\nНапример: `/remove_admin @ivan`", parse_mode="Markdown")
        return

    username = parts[1]
    if not username.startswith('@'):
        bot.reply_to(message, "❌ Укажите @username")
        return

    try:
        user_info = bot.get_chat(username)
        user_id = user_info.id
        
        admins = load_admins()
        if user_id not in admins:
            bot.reply_to(message, f"⚠️ Пользователь {username} не является админом.")
            return
        
        admins.remove(user_id)
        save_admins(admins)
        bot.reply_to(message, f"✅ Пользователь {username} удалён из админов!")
        
    except Exception as e:
        bot.reply_to(
            message,
            f"❌ Не удалось найти пользователя {username}.\n\n"
            f"Удалите ID вручную из файла `admins.json`",
            parse_mode="Markdown"
        )

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
        # Пытаемся получить username по ID
        try:
            user = bot.get_chat(admin_id)
            username = user.username or f"ID: {admin_id}"
        except:
            username = f"ID: {admin_id}"
        text += f"{i}. @{username}\n"
    
    text += f"\n👑 Владелец: `{OWNER_ID}`"

    bot.reply_to(message, text, parse_mode="Markdown")
