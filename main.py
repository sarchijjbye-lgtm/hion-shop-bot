from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
from oils_data import OILS
from google_sheets import connect_to_sheet, add_order
from config import BOT_TOKEN, ADMIN_CHAT_ID, GROUP_CHAT_ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)

user_carts = {}
sheet = connect_to_sheet()

@app.route('/')
def home():
    return "HION Bot is running."

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = InlineKeyboardMarkup()
    for name in OILS.keys():
        markup.add(InlineKeyboardButton(name, callback_data=f"oil_{name}"))
    await message.answer(
        "Добро пожаловать в HION - местное производство и авторская продукция.\n"
        "Выберите продукт, чтобы узнать подробнее или оформить заказ.",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data.startswith("oil_"))
async def oil_info(callback: types.CallbackQuery):
    name = callback.data[4:]
    oil = OILS[name]
    text = f"*{name}*\n\n{oil['desc']}"
    markup = InlineKeyboardMarkup()
    for vol, price in oil['prices'].items():
        markup.add(InlineKeyboardButton(f"{vol} — {price}₽", callback_data=f"add_{name}_{vol}_{price}"))
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("add_"))
async def add_item(callback: types.CallbackQuery):
    _, name, vol, price = callback.data.split("_", 3)
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append((name, vol, int(price)))
    await callback.answer("✅ Добавлено в корзину")

@dp.callback_query_handler(lambda c: c.data == "back")
async def back(callback: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    for name in OILS.keys():
        markup.add(InlineKeyboardButton(name, callback_data=f"oil_{name}"))
    await callback.message.edit_text(
        "🌿 Выберите продукт, чтобы узнать подробнее или оформить заказ.",
        reply_markup=markup
    )

@dp.message_handler(commands=['cart'])
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    if not cart:
        await message.answer("Корзина пуста 🧺")
        return
    total = sum(p for _, _, p in cart)
    text = "\n".join([f"{n} {v} — {p}₽" for n, v, p in cart])
    text += f"\n\n💰 Итого: {total}₽"
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💳 Оплатить через @CkPayBot", url=f"https://t.me/CkPayBot?start=pay_123456_{total}"))
    await message.answer(text, reply_markup=markup)

@dp.message_handler(lambda m: m.text.lower().startswith("адрес"))
async def save_address(message: types.Message):
    user_id = message.from_user.id
    address = message.text.replace("Адрес:", "").strip()
    cart = user_carts.get(user_id, [])
    if not cart:
        await message.answer("Сначала добавьте товары 🛒")
        return
    total = sum(p for _, _, p in cart)
    items = "; ".join([f"{n} {v} — {p}₽" for n, v, p in cart])
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    add_order(sheet, username, items, address, total, "Ожидает оплаты")

    order_text = f"🛍 Новый заказ:\n{items}\n\n💰 Сумма: {total}₽\n📍 Адрес: {address}\n👤 {username}"
    await bot.send_message(ADMIN_CHAT_ID, order_text)
    if GROUP_CHAT_ID != 0:
        await bot.send_message(GROUP_CHAT_ID, order_text)
    user_carts[user_id] = []
    await message.answer("Спасибо! Ваш заказ зарегистрирован. Для оплаты используйте кнопку в корзине 💛")

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    executor.start_polling(dp)
