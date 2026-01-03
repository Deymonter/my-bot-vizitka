import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

# --- ТВОИ ДАННЫЕ ---
BOT_TOKEN = "8512918115:AAEjvtjEvpmyIR72dK77t3G2wwltqZCHlV8"
MY_LINK = "https://t.me/ShermentaI"

logging.basicConfig(level=logging.INFO)

# --- УМНАЯ НАСТРОЙКА ПРОКСИ ---
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    session = AiohttpSession(proxy="http://proxy.server:3128")
else:
    session = None

bot = Bot(
    token=BOT_TOKEN,
    session=session, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === ЖУРНАЛ СООБЩЕНИЙ ===
users_msg_stack = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Услуги и Цены", callback_data="services"))
    builder.row(types.InlineKeyboardButton(text="Калькулятор стоимости", callback_data="calc_start"))
    builder.row(types.InlineKeyboardButton(text="Написать мне", url=MY_LINK)) 
    return builder.as_markup()

def get_start_button():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

async def clean_chat(chat_id: int, user_id: int):
    if user_id in users_msg_stack:
        for msg_id in users_msg_stack[user_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        users_msg_stack[user_id] = []

def add_msg_to_stack(user_id, msg_id):
    if user_id not in users_msg_stack:
        users_msg_stack[user_id] = []
    users_msg_stack[user_id].append(msg_id)

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await clean_chat(message.chat.id, user_id)
    try:
        await message.delete()
    except:
        pass

    msg1 = await message.answer(
        "👋 <b>Приветствую</b>\n"
        "Я Python-разработчик. Автоматизирую рутину и создаю удобные инструменты.\n"
        "Внизу кнопка для сброса.",
        reply_markup=get_start_button() 
    )
    
    msg2 = await message.answer(
        "Чем могу быть полезен?",
        reply_markup=get_main_menu()
    )
    
    add_msg_to_stack(user_id, msg1.message_id)
    add_msg_to_stack(user_id, msg2.message_id)

@dp.message(F.text == "🏠 Главное меню")
async def menu_button_click(message: types.Message):
    await cmd_start(message)

@dp.callback_query(F.data == "back_home")
async def go_back(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "👋 <b>Главное меню:</b>\n"
            "Чем могу быть полезен?",
            reply_markup=get_main_menu()
        )
    except:
        msg = await callback.message.answer("👋 <b>Главное меню:</b>", reply_markup=get_main_menu())
        add_msg_to_stack(callback.from_user.id, msg.message_id)
    await callback.answer()

@dp.callback_query(F.data == "services")
async def send_services(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📩 Заказать", url=MY_LINK))
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_home"))
    
    text = (
        "🛠 <b>Мои услуги:</b>\n\n"
        "<b>Telegram-боты</b>\n"
        "Магазины, визитки, воронки продаж.\n"
        "💵 <i>от 800 грн</i>\n\n"
        "<b>Парсинг (Сбор данных)</b>\n"
        "Выгрузка товаров, цен, контактов в Excel.\n"
        "💵 <i>от 1000 грн</i>\n\n"
        "<b>Скрипты автоматизации</b>\n"
        "Рассылки, обработка файлов, авто-постинг.\n"
        "💵 <i>от 1500 грн</i>"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# === ЛОГИКА КАЛЬКУЛЯТОРА ===

# Шаг 1: Выбор категории
@dp.callback_query(F.data == "calc_start")
async def calc_step_1(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Чат-бот", callback_data="cat_bots"))
    builder.row(types.InlineKeyboardButton(text="Парсинг", callback_data="cat_parsing"))
    builder.row(types.InlineKeyboardButton(text="Скрипт", callback_data="cat_script"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_home"))
    
    await callback.message.edit_text("Что нужно разработать?", reply_markup=builder.as_markup())
    await callback.answer()

# Шаг 2: Выбор сложности (зависит от категории)
@dp.callback_query(F.data.startswith("cat_"))
async def calc_step_2(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    category = callback.data
    
    if category == "cat_bots":
        # Если выбрали Ботов
        builder.row(types.InlineKeyboardButton(text="Визитка / Меню", callback_data="res_bot_simple"))
        builder.row(types.InlineKeyboardButton(text="Магазин / Админка", callback_data="res_bot_hard"))
        text = "Какой функционал нужен боту?"
        
    elif category == "cat_parsing":
        # Если выбрали Парсинг
        builder.row(types.InlineKeyboardButton(text="Простой сайт", callback_data="res_parse_simple"))
        builder.row(types.InlineKeyboardButton(text="Сложный (с логином)", callback_data="res_parse_hard"))
        text = "С какого сайта собираем данные?"
        
    elif category == "cat_script":
        # Если выбрали Скрипт
        builder.row(types.InlineKeyboardButton(text="Простая задача", callback_data="res_script_simple"))
        builder.row(types.InlineKeyboardButton(text="Сложная система", callback_data="res_script_hard"))
        text = "Насколько сложная автоматизация?"

    builder.row(types.InlineKeyboardButton(text="🔙 К выбору типа", callback_data="calc_start"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

# Шаг 3: Результат (Цены)
@dp.callback_query(F.data.startswith("res_"))
async def calc_final(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="📩 Обсудить задачу", url=MY_LINK))
    builder.add(types.InlineKeyboardButton(text="🔙 В начало", callback_data="calc_start"))
    
    choice = callback.data
    
    # БОТЫ
    if choice == "res_bot_simple":
        price = "800 - 1500 грн"
        time = "1-2 дня"
        desc = "Бот-визитка, ответы на вопросы, простая навигация."
    elif choice == "res_bot_hard":
        price = "от 2500 грн"
        time = "5-10 дней"
        desc = "Корзина товаров, админ-панель, база данных, интеграция с таблицами."
        
    # ПАРСИНГ
    elif choice == "res_parse_simple":
        price = "800 - 1200 грн"
        time = "1 день"
        desc = "Сбор текста/цен с открытого сайта (без капчи и регистрации)."
    elif choice == "res_parse_hard":
        price = "от 2000 грн"
        time = "3-5 дней"
        desc = "Сайты с защитой, необходимостью входа в аккаунт, динамические данные."
        
    # СКРИПТЫ
    elif choice == "res_script_simple":
        price = "1000 - 1500 грн"
        time = "1-2 дня"
        desc = "Сортировка файлов, рассылка сообщений, простые вычисления."
    elif choice == "res_script_hard":
        price = "от 3000 грн"
        time = "от 5 дней"
        desc = "Работа с PDF, сложные отчеты, управление браузером, работа с API."

    text = (
        f"<b>Примерная оценка:</b>\n\n"
        f"Стоимость: <b>{price}</b>\n"
        f"Срок: <b>{time}</b>\n\n"
        f"📝 <i>{desc}</i>\n\n"
        "Напишите мне для точного расчета."
    )
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

async def main():
    print("Бот ShermentaI (v5.0 Full Calculator) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
