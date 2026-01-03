import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# --- ТВОИ ДАННЫЕ (УЖЕ ЗАПОЛНЕНЫ) ---
BOT_TOKEN = "8512918115:AAEjvtjEvpmyIR72dK77t3G2wwltqZCHlV8"
MY_LINK = "https://t.me/ShermentaI"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Создаем бота с HTML-разметкой
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ФУНКЦИЯ: ГЛАВНОЕ МЕНЮ (чтобы использовать в разных местах) ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛠 Услуги", callback_data="services"))
    builder.row(types.InlineKeyboardButton(text="📂 Портфолио", callback_data="portfolio"))
    builder.row(types.InlineKeyboardButton(text="💰 Узнать цену", callback_data="calc_start"))
    builder.row(types.InlineKeyboardButton(text="📩 Написать мне", url=MY_LINK)) 
    return builder.as_markup()

# --- ХЕНДЛЕРЫ (ОБРАБОТЧИКИ) ---

# 1. Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Приветствую!</b>\n"
        "Я бот-визитка. Здесь вы можете узнать о моих услугах и посмотреть примеры работ.\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )

# 2. Кнопка "НАЗАД" (Возвращает в главное меню)
@dp.callback_query(F.data == "back_home")
async def go_back(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "👋 <b>Главное меню:</b>\n"
            "Чем могу помочь?",
            reply_markup=get_main_menu()
        )
    except:
        # Если сообщение нельзя отредактировать (например, это было фото), шлем новое
        await callback.message.answer(
            "👋 <b>Главное меню:</b>",
            reply_markup=get_main_menu()
        )
    await callback.answer()

# 3. Раздел УСЛУГИ
@dp.callback_query(F.data == "services")
async def send_services(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_home"))
    
    await callback.message.edit_text(
        "🛠 <b>Мои услуги:</b>\n\n"
        "🔹 <b>Чат-боты под ключ</b> (Магазины, Визитки, Админы)\n"
        "🔹 <b>Парсинг данных</b> (Сбор информации с сайтов)\n"
        "🔹 <b>Скрипты автоматизации</b> (Python)",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# 4. Раздел ПОРТФОЛИО
@dp.callback_query(F.data == "portfolio")
async def send_portfolio(callback: types.CallbackQuery):
    # Удаляем старое текстовое меню, чтобы не мешало
    await callback.message.delete()
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Скрыть и вернуться", callback_data="delete_photo_back"))
    
    # Отправляем фото
    await callback.message.answer_photo(
        photo="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
        caption="📂 <b>Пример работы:</b>\n\nЭто демонстрация отправки медиа-файлов. В реальном проекте здесь будет скриншот вашего бота.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Обработка возврата из меню с картинкой
@dp.callback_query(F.data == "delete_photo_back")
async def delete_photo_back(callback: types.CallbackQuery):
    await callback.message.delete() # Удаляем фото
    await callback.message.answer(  # Шлем меню заново
        "👋 <b>Главное меню:</b>",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# 5. КАЛЬКУЛЯТОР
@dp.callback_query(F.data == "calc_start")
async def calc_step_1(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Простой (Визитка)", callback_data="price_simple"))
    builder.row(types.InlineKeyboardButton(text="Сложный (Магазин)", callback_data="price_hard"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_home"))
    
    await callback.message.edit_text("Какой тип бота вас интересует?", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("price_"))
async def calc_result(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 В меню", callback_data="back_home"))

    if callback.data == "price_simple":
        text = "📊 <b>Расчет:</b>\n💰 Цена: ~800 грн.\n⏳ Срок: 1-2 дня."
    else:
        text = "📊 <b>Расчет:</b>\n💰 Цена: от 2000 грн.\n⏳ Срок: 3-5 дней."
        
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# --- ЗАПУСК ---
async def main():
    print("Бот ShermentaI запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")