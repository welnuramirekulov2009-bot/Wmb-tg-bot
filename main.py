import asyncio  # Shu yerda 'i' harfi kichik bo'lishi shart
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- SOZLAMALAR ---
TOKEN = "7754146413:AAFDWuKaTGYnc2XjMYRmSYnQEHbVXlSCZSk"
ADMIN_ID = 6479727191 

# Kanallar va Havolalar
CHANNELS = [
    {"name": "1-Kanal (Obuna bo'ling)", "url": "https://t.me/UZGEND_WORLDMINEBOY", "id": "@UZGEND_WORLDMINEBOY"},
    {"name": "YouTube (Obuna bo'ling)", "url": "https://youtube.com/@mineboyuz?si=-7ppaMbBupT-Tv_Y", "id": None},
    {"name": "Zaxira Kanal", "url": "https://t.me/UZGEND_WORLDMINEBOY", "id": "@UZGEND_WORLDMINEBOY"}
]

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect("minecraft_contest.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, phone TEXT, nick TEXT)")
    conn.commit()
    conn.close()

class Register(StatesGroup):
    waiting_for_phone = State()
    waiting_for_nick = State()

# Obunani tekshirish funksiyasi
async def check_subscription(user_id):
    for ch in CHANNELS:
        if ch["id"]: 
            try:
                member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
                if member.status in ["left", "kicked"]:
                    return False
            except Exception as e:
                logging.error(f"Xatolik: {e}")
                return False
    return True

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    if await check_subscription(message.from_user.id):
        caption = (
            "🎮 **Minecraft Musobaqasiga Xush Kelibsiz!**\n\n"
            "Musobaqada qatnashish uchun quyidagi ma'lumotlarni to'ldiring.\n"
            "Avval telefon raqamingizni yuboring, keyin Nicknamingizni."
        )
        # O'zingizning Minecraft rasmingiz linkini shu yerga qo'ying
        photo_url = "https://i.ytimg.com/vi/your_thumbnail/maxresdefault.jpg" 
        
        btn = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
        
        try:
            await message.answer_photo(photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=btn)
        except:
            await message.answer(caption, parse_mode="Markdown", reply_markup=btn)
        
        await state.set_state(Register.waiting_for_phone)
    else:
        kb = []
        for ch in CHANNELS:
            kb.append([InlineKeyboardButton(text=ch["name"], url=ch["url"])])
        kb.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")])
        
        markup = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer("Musobaqada qatnashish uchun avval quyidagilarga obuna bo'ling:", reply_markup=markup)

@dp.callback_query(F.data == "check")
async def check_callback(call: types.CallbackQuery, state: FSMContext):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await start(call.message, state)
    else:
        await call.answer("Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

@dp.message(Register.waiting_for_phone, F.contact)
async def phone_received(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("✅ Raqam qabul qilindi! Endi Minecraftdagi **Nickname**ingizni yozing:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Register.waiting_for_nick)

@dp.message(Register.waiting_for_nick)
async def nick_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data['phone']
    nick = message.text
    user_id = message.from_user.id
    
    conn = sqlite3.connect("minecraft_contest.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (user_id, phone, nick))
    conn.commit()
    conn.close()
    
    await message.answer(f"🚀 **Ajoyib!** Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n📞 Tel: {phone}\n🎮 Nickname: {nick}\n\nMusobaqada omad tilaymiz!")
    await state.clear()

@dp.message(Command("stat"))
async def get_stat(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect("minecraft_contest.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        await message.answer(f"📊 Jami ro'yxatdan o'tganlar: **{count}** kishi.")

@dp.message(Command("settings"))
async def settings(message: types.Message, state: FSMContext):
    await message.answer("Yangi Minecraft Nicknamingizni yozing:")
    await state.set_state(Register.waiting_for_nick)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
