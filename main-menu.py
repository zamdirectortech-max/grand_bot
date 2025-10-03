from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8346101623:AAGOAzzq3MP6xziGXd8zZnhRcb83uCNYzR4"

user_languages = {}

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    await update.message.reply_text("👋 Тілді таңдаңыз / Выберите язык / Choose language:", reply_markup=markup)

# --- Обработка выбора языка ---
async def callback_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_languages[query.from_user.id] = lang

    if lang == "ru":
        text = "Добро пожаловать в официальный чат-бот ЮКУ им. М.О. Ауэзова! 👋\n\nВыберите раздел:"
        buttons = [
            ("🎓 Абитуриентам", "menu_applicants"),
            ("🎓 Студентам", "menu_students"),
            ("📞 Контакты", "menu_contacts"),
            ("❓ Задать вопрос ИИ", "menu_ai"),
            ("🌐 Сменить язык", "menu_lang")
        ]
    elif lang == "kz":
        text = "Қош келдіңіз ресми чат-ботқа М.О. Әуезов атындағы ОҚУ! 👋\n\nМәзірден бөлімді таңдаңыз:"
        buttons = [
            ("🎓 Талапкерлерге", "menu_applicants"),
            ("🎓 Студенттерге", "menu_students"),
            ("📞 Байланыс", "menu_contacts"),
            ("❓ Сұрақ қою AI", "menu_ai"),
            ("🌐 Тілді ауыстыру", "menu_lang")
        ]
    else:
        text = "Welcome to the official chatbot of M.Auezov South Kazakhstan University! 👋\n\nChoose a section:"
        buttons = [
            ("🎓 For Applicants", "menu_applicants"),
            ("🎓 For Students", "menu_students"),
            ("📞 Contacts", "menu_contacts"),
            ("❓ Ask AI", "menu_ai"),
            ("🌐 Change Language", "menu_lang")
        ]

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(bt, callback_data=cb)] for bt, cb in buttons])

    # редактируем предыдущее сообщение, не создаём новое
    await query.edit_message_text(text=text, reply_markup=markup)

# --- Обработка меню ---
async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_languages.get(query.from_user.id, "ru")

    if query.data == "menu_lang":
        # возврат к выбору языка
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
        ])
        await query.edit_message_text("👋 Тілді таңдаңыз / Выберите язык / Choose language:", reply_markup=markup)
        return

    texts = {
        "menu_applicants": {
            "ru": "Информация для абитуриентов...",
            "kz": "Талапкерлерге арналған ақпарат...",
            "en": "Information for applicants..."
        },
        "menu_students": {
            "ru": "Информация для студентов...",
            "kz": "Студенттерге арналған ақпарат...",
            "en": "Information for students..."
        },
        "menu_contacts": {
            "ru": "Контакты университета...",
            "kz": "Университеттің байланыс нөмірлері...",
            "en": "University contact information..."
        },
        "menu_ai": {
            "ru": "Напишите ваш вопрос, и я попробую ответить.",
            "kz": "Сұрағыңызды жазыңыз, жауап беруге тырысамын.",
            "en": "Type your question, and I’ll try to answer."
        }
    }

    text = texts[query.data][lang]
    await query.edit_message_text(text=text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(callback_menu, pattern="^menu_"))
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
