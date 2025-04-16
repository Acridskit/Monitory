import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Этапы разговора
(SL_ZONE, SL_DATA, B100_DATA) = range(3)

user_data = {}

sl90_fields = [
    "Количество ТС", "Запрет аренды", "В доступе", "НЗ", "Меньше 50%", "Больше 50%",
    "Меньше 30%", "Меньше 5%", "Нет связи", "Нет GPS", "Критическая ошибка",
    "Требует ремонта", "Тревога", "Авторемонт", "Перемещения", "Забытые перемещения",
    "Забытое НЗ", "Простой 24ч", "Ремонт", "Готов к эксплуатации", "Простой статус",
    "Транспорт украден", "Чарджеры Л/А", "Чарджеры Н/А", "Чарджеры на самокате", "Ошибка GPS"
]

b100_fields = [
    "Количество ТС", "Запрет аренды", "В доступе", "НЗ", "Меньше 50%", "Больше 50%",
    "Меньше 30%", "Меньше 5%", "Нет связи", "Нет GPS", "Критическая ошибка",
    "Требует ремонта", "Простой"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пора делать мониторинг. Укажи техническую зону (например, Речной)")
    return SL_ZONE

async def sl_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['zone'] = update.message.text
    context.user_data['sl90'] = {}
    context.user_data['sl90_index'] = 0
    await update.message.reply_text(f"Введи значение: {sl90_fields[0]}")
    return SL_DATA

async def sl_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data['sl90_index']
    context.user_data['sl90'][sl90_fields[idx]] = update.message.text
    idx += 1
    if idx < len(sl90_fields):
        context.user_data['sl90_index'] = idx
        await update.message.reply_text(f"Введи значение: {sl90_fields[idx]}")
        return SL_DATA
    else:
        context.user_data['b100'] = {}
        context.user_data['b100_index'] = 0
        await update.message.reply_text(f"Теперь введи данные по B100. Введи значение: {b100_fields[0]}")
        return B100_DATA

async def b100_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data['b100_index']
    context.user_data['b100'][b100_fields[idx]] = update.message.text
    idx += 1
    if idx < len(b100_fields):
        context.user_data['b100_index'] = idx
        await update.message.reply_text(f"Введи значение: {b100_fields[idx]}")
        return B100_DATA
    else:
        text = generate_report(context.user_data)
        await update.message.reply_text("Готово! Вот твой мониторинг:")
        await update.message.reply_text(text)
        return ConversationHandler.END

def generate_report(data):
    zone = data['zone']
    sl = data['sl90']
    b = data['b100']
    
    sl_text = f"{zone}\nSL 90\n"
    for k, v in sl.items():
        sl_text += f"{k} - {v}\n"

    b_text = f"\nB-100\n"
    for k, v in b.items():
        b_text += f"{k} - {v}\n"

    return sl_text + b_text

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Мониторинг отменён.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        SL_ZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sl_zone)],
        SL_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sl_data)],
        B100_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, b100_data)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

def main():
    import os
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(conv_handler)

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.bot.send_message(chat_id=113712480, text="Пора делать мониторинг! Напиши /start"), 'cron', hour=6, minute=30)
    scheduler.add_job(lambda: app.bot.send_message(chat_id=113712480, text="Пора делать вечерний мониторинг! Напиши /start"), 'cron', hour=18, minute=30)
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()
