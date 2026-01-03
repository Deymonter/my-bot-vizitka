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

# === ЖУРНАЛ СООБЩЕНИЙ (Чтобы удалять всё лишнее) ===
# Формат: {user_id: [id_сообщения_1, id_сообщения_2, ...]}
users_msg_stack = {}

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

# Функция: Полная очистка чата от старых сообщений бота
async def clean_chat(chat_id: int, user_id: int):
    if user_id in users_msg_stack:
        for msg_id in users_msg_stack[user_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        # Очищаем список после удаления
        users_msg_stack[user_id] = []

# Функция: Добавить сообщение в список на удаление
def add_msg_to_stack(user_id, msg_id):
    if user_id not in users_msg_stack:
        users_msg_stack[user_id] = []
    users_msg_stack[user_id].append(msg_id)

# --- ХЕНДЛЕРЫ ---

# 1. ГЛАВНОЕ МЕНЮ (СТАРТ)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Удаляем ВСЕ старые сообщения бота
    await clean_chat(message.chat.id, user_id)
    
    # 2. Удаляем сообщение юзера "/start" (или "Главное меню")
    try:
        await message.delete()
    except:
        pass

    # 3. Отправляем приветствие (Сообщение №1)
    msg1 = await message.answer(
        "👋 <b>Приветствую!</b>\n"
        "Я бот-визитка. Чтобы не потеряться, внизу теперь есть кнопка меню.",
        reply_markup=get_start_button() 
    )
    
    # 4. Отправляем меню с кнопками (Сообщение №2)
    msg2 = await message.answer(
        "Выберите раздел:",
        reply_markup=get_main_menu()
    )
    
    # Запоминаем ОБА сообщения, чтобы потом удалить их оба
    add_msg_to_stack(user_id, msg1.message_id)
    add_msg_to_stack(user_id, msg2.message_id)

# 2. Обработка нажатия на нижнюю кнопку
@dp.message(F.text == "🏠 Главное меню")
async def menu_button_click(message: types.Message):
    await cmd_start(message)

# 3. Кнопка "НАЗАД" (Редактирует нижнее сообщение)
@dp.callback_query(F.data == "back_home")
async def go_back(callback: types.CallbackQuery):
    try:
        # Редактируем только нижнее сообщение (меню)
        await callback.message.edit_text(
            "👋 <b>Главное меню:</b>\n"
            "Чем могу помочь?",
            reply_markup=get_main_menu()
        )
    except:
        # Если редактировать нельзя, шлем новое и запоминаем его
        msg = await callback.message.answer("👋 <b>Главное меню:</b>", reply_markup=get_main_menu())
        add_msg_to_stack(callback.from_user.id, msg.message_id)
        
    await callback.answer()

# 4. УСЛУГИ
@dp.callback_query(F.data == "services")
async def send_services(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_home"))
    
    await callback.message.edit_text(
        "🛠 <b>Мои услуги:</b>\n\n"
        "🔹 <b>Чат-боты под ключ</b> (Магазины, Визитки)\n"
        "🔹 <b>Парсинг данных</b>\n"
        "🔹 <b>Автоматизация</b>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# 5. ПОРТФОЛИО (Фото)
@dp.callback_query(F.data == "portfolio")
async def send_portfolio(callback: types.CallbackQuery):
    # Удаляем текстовое меню
    await callback.message.delete()
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Скрыть и вернуться", callback_data="delete_photo_back"))
    
    # Шлем фото
    photo_msg = await callback.message.answer_photo(
        photo="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
        caption="📂 <b>Пример работы:</b>\n\nЗдесь будет ваш проект.",
        reply_markup=builder.as_markup()
    )
    # Добавляем фото в список "на удаление" при следующем старте
    add_msg_to_stack(callback.from_user.id, photo_msg.message_id)
    await callback.answer()

@dp.callback_query(F.data == "delete_photo_back")
async def delete_photo_back(callback: types.CallbackQuery):
    await callback.message.delete() 
    # Возвращаем меню
    msg = await callback.message.answer(
        "👋 <b>Главное меню:</b>",
        reply_markup=get_main_menu()
    )
    add_msg_to_stack(callback.from_user.id, msg.message_id)
    await callback.answer()

# 6. КАЛЬКУЛЯТОР
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
    print("Бот ShermentaI (Clean Version) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
