from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import datetime, json, openpyxl, os
from difflib import get_close_matches  # для умного поиска

# --- Конфигурация ---
TOKEN = "8346101623:AAGOAzzq3MP6xziGXd8zZnhRcb83uCNYzR4"
ADMIN_ID = 8211811011

# --- Файлы ---
USERS_FILE = "users.json"
QUESTIONS_FILE = "questions.json"
KNOWLEDGE_FILE = "knowledge.json"

# --- Память ---
user_languages = {}
knowledge = {}
users = []
questions_log = []


# ====== Работа с файлами ======
def load_data():
    global knowledge, users, questions_log
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            knowledge = json.load(f)
    else:
        knowledge = {}

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    else:
        users = []

    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            questions_log = json.load(f)
    else:
        questions_log = []


def save_data():
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(questions_log, f, ensure_ascii=False, indent=2)


# ====== Логика ======
def chatbot(user_text: str):
    """Умный поиск по базе знаний"""
    questions = list(knowledge.keys())
    matches = get_close_matches(user_text.lower(), [q.lower() for q in questions], n=1, cutoff=0.5)
    if matches:
        # ищем оригинальный ключ (с учётом регистра)
        for q, a in knowledge.items():
            if q.lower() == matches[0]:
                return a
    return None


def add_user(user):
    """Добавляем пользователя, если он новый"""
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        save_data()


def log_question(user_id, username, text):
    questions_log.append({
        "user_id": user_id,
        "username": username,
        "text": text,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_data()


# ====== Команды ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)  # записываем пользователя
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    await update.message.reply_text("👋 Тілді таңдаңыз / Выберите язык / Choose language:", reply_markup=markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        text = (
            "📌 Команды админа:\n"
            "/export – выгрузить вопросы за неделю (Excel)\n"
            "/add вопрос || ответ – добавить новый ответ\n"
            "/users – список пользователей\n"
            "/stats – статистика\n"
            "/broadcast текст – рассылка всем\n\n"
            "📌 Команды пользователей:\n/start, /help"
        )
    else:
        text = "📌 Команды пользователей:\n/start – меню\n/help – помощь"
    await update.message.reply_text(text)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Нет доступа.")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Вопросы"
    ws.append(["ID пользователя", "Имя", "Вопрос", "Дата"])

    for q in questions_log:
        ws.append([q["user_id"], q["username"], q["text"], q["date"]])

    file_name = "questions.xlsx"
    wb.save(file_name)
    await update.message.reply_document(open(file_name, "rb"))


async def add_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Нет прав.")
    try:
        text = update.message.text.replace("/add ", "", 1)
        question, answer = text.split("||")
        knowledge[question.strip()] = answer.strip()
        save_data()
        await update.message.reply_text("✅ Ответ добавлен.")
    except Exception:
        await update.message.reply_text("⚠ Формат: /add вопрос || ответ")


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = "👥 Пользователи:\n"
    for u in users:
        text += f"{u['id']} – @{u['username']} ({u['first_name']})\n"
    await update.message.reply_text(text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = (
        f"📊 Статистика:\n"
        f"Пользователей: {len(users)}\n"
        f"Вопросов: {len(questions_log)}"
    )
    await update.message.reply_text(text)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text.replace("/broadcast ", "", 1)
    for u in users:
        try:
            await context.bot.send_message(u["id"], f"📢 Сообщение от админа:\n\n{text}")
        except Exception:
            pass
    await update.message.reply_text("✅ Рассылка выполнена.")


# ====== Меню ======
async def show_main_menu(query, lang):
    if lang == "ru":
        text = "Добро пожаловать! 👋 Выберите раздел:"
        buttons = [
            ("🎓 Абитуриентам", "menu_applicants"),
            ("🎓 Студентам", "menu_students"),
            ("📞 Контакты", "menu_contacts"),
            ("❓ Задать вопрос ИИ", "menu_ai"),
            ("🌐 Сменить язык", "menu_lang")
        ]
    elif lang == "kz":
        text = "Қош келдіңіз! 👋 Мәзірден таңдаңыз:"
        buttons = [
            ("🎓 Талапкерлерге", "menu_applicants"),
            ("🎓 Студенттерге", "menu_students"),
            ("📞 Байланыс", "menu_contacts"),
            ("❓ AI сұрау", "menu_ai"),
            ("🌐 Тілді ауыстыру", "menu_lang")
        ]
    else:
        text = "Welcome! 👋 Choose a section:"
        buttons = [
            ("🎓 For Applicants", "menu_applicants"),
            ("🎓 For Students", "menu_students"),
            ("📞 Contacts", "menu_contacts"),
            ("❓ Ask AI", "menu_ai"),
            ("🌐 Change Language", "menu_lang")
        ]
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(bt, callback_data=cb)] for bt, cb in buttons])
    await query.edit_message_text(text=text, reply_markup=markup)


async def callback_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_languages[query.from_user.id] = lang
    await show_main_menu(query, lang)


async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_languages.get(query.from_user.id, "ru")

    if query.data == "menu_applicants":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📑 Документы", callback_data="app_docs")],
            [InlineKeyboardButton("💰 Гранты", callback_data="app_grants")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.edit_message_text("📌 Раздел для абитуриентов:", reply_markup=markup)

    elif query.data == "menu_students":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Учеба", callback_data="stud_study")],
            [InlineKeyboardButton("💳 Стипендии", callback_data="stud_grants")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ])
        await query.edit_message_text("📌 Раздел для студентов:", reply_markup=markup)

    elif query.data == "menu_ai":
        await query.edit_message_text("❓ Напишите ваш вопрос:")
        context.user_data["ask_ai"] = True

    elif query.data == "main_menu":
        await show_main_menu(query, lang)


# ====== Тексты ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id

    if context.user_data.get("ask_ai"):
        context.user_data["ask_ai"] = False
        response = chatbot(user_text)
        if response:
            await update.message.reply_text(response)
        else:
            log_question(user_id, update.effective_user.username, user_text)
            await update.message.reply_text("🤔 Пока не знаю. Запрос сохранён, скоро подготовим ответ.")
        return

    await update.message.reply_text("Используйте меню ниже 👇 (/start для главного меню)")


# ====== Запуск ======
def main():
    load_data()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("add", add_answer))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(callback_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern=".*"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
