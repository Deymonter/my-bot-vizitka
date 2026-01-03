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

# === ПАМЯТЬ БОТА (Словарь для хранения ID последних сообщений) ===
# Структура: {user_id: message_id}
users_last_msg = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛠 Услуги", callback_data="services"))
    builder.row(types.InlineKeyboardButton(text="📂 Портфолио", callback_data="portfolio"))
    builder.row(types.InlineKeyboardButton(text="💰 Узнать цену", callback_data="calc_start"))
    builder.row(types.InlineKeyboardButton(text="📩 Написать мне", url=MY_LINK)) 
    return builder.as_markup()

def get_start_button():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

# Функция для удаления старого сообщения (очистка чата)
async def clear_previous_message(chat_id: int, user_id: int):
    # Если у нас записано старое сообщение для этого юзера
    if user_id in users_last_msg:
        old_msg_id = users_last_msg[user_id]
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except:
            # Если сообщение уже удалено или слишком старое, просто игнорируем ошибку
            pass

# --- ХЕНДЛЕРЫ ---

# 1. Обработка команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Сначала удаляем старое меню, если оно было
    await clear_previous_message(message.chat.id, user_id)
    
    # Удаляем само сообщение "/start", которое написал юзер (для красоты)
    try:
        await message.delete()
    except:
        pass

    # Отправляем новое сообщение
    sent_msg = await message.answer(
        "👋 <b>Приветствую!</b>\n"
        "Я бот-визитка. Чтобы не потеряться, внизу есть кнопка меню.",
        reply_markup=get_start_button() 
    )
    
    # Отправляем инлайн-меню
    menu_msg = await message.answer(
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )
    
    # Запоминаем ID этого меню, чтобы потом его удалить
    users_last_msg[user_id] = menu_msg.message_id

# 2. Обработка нажатия на кнопку "🏠 Главное меню"
@dp.message(F.text == "🏠 Главное меню")
async def menu_button_click(message: types.Message):
    # Удаляем текст "🏠 Главное меню", который отправил юзер
    try:
        await message.delete()
    except:
        pass
        
    # Запускаем логику старта (она сама почистит старое меню бота)
    await cmd_start(message)

# 3. Кнопка "НАЗАД"
@dp.callback_query(F.data == "back_home")
async def go_back(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text(
            "👋 <b>Главное меню:</b>\n"
            "Чем могу помочь?",
            reply_markup=get_main_menu()
        )
    except:
        new_msg = await callback.message.answer(
            "👋 <b>Главное меню:</b>",
            reply_markup=get_main_menu()
        )
        # Если пришлось отправить новое, обновляем запись в памяти
        users_last_msg[callback.from_user.id] = new_msg.message_id
        
    await callback.answer()

# 4. Остальные разделы
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

@dp.callback_query(F.data == "portfolio")
async def send_portfolio(callback: types.CallbackQuery):
    await callback.message.delete()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Скрыть и вернуться", callback_data="delete_photo_back"))
    
    # Отправляем фото
    photo_msg = await callback.message.answer_photo(
        photo="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
        caption="📂 <b>Пример работы:</b>\n\nВ реальном проекте здесь будет скриншот вашего бота.",
        reply_markup=builder.as_markup()
    )
    # Запоминаем ID фото, так как теперь это главное активное сообщение
    users_last_msg[callback.from_user.id] = photo_msg.message_id
    await callback.answer()

@dp.callback_query(F.data == "delete_photo_back")
async def delete_photo_back(callback: types.CallbackQuery):
    await callback.message.delete() 
    menu_msg = await callback.message.answer(
        "👋 <b>Главное меню:</b>",
        reply_markup=get_main_menu()
    )
    users_last_msg[callback.from_user.id] = menu_msg.message_id
    await callback.answer()

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

async def main():
    print("Бот ShermentaI (v2.0 Clean) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
