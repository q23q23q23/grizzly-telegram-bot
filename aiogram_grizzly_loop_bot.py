import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_KEY = "442e157e46a57c44ffb292ba03da08be"
BOT_TOKEN = "8037340967:AAH-hUbEwJhnlPQlcAlVq8kl1Fa2AWKhTNc"
WAIT_FOR_SMS = 120

COUNTRIES = {
    "🇦🇪 الإمارات": "0",
    "🇷🇺 روسيا": "7",
    "🇺🇸 أمريكا": "1",
    "🇮🇩 إندونيسيا": "62",
    "🇺🇦 أوكرانيا": "380"
}

SERVICES = {
    "Telegram": "tg",
    "WhatsApp": "wa",
    "Gmail": "go"
}

user_config = {}
active_loops = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_keyboard(options: dict, prefix: str, multi=False, selected=None):
    if not selected:
        selected = []
    builder = InlineKeyboardBuilder()
    for label, value in options.items():
        emoji = "✅ " if value in selected else ""
        builder.button(text=f"{emoji}{label}", callback_data=f"{prefix}:{value}")
    if multi:
        builder.button(text="✅ احفظ وابدأ", callback_data="confirm")
    return builder.as_markup()

def send_telegram_msg(chat_id, text):
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     params={"chat_id": chat_id, "text": text})
    except:
        pass

def get_sms_code(activation_id):
    for _ in range(WAIT_FOR_SMS // 5):
        url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={activation_id}"
        res = requests.get(url).text
        if "STATUS_OK" in res:
            return res.split(":")[1]
        asyncio.sleep(5)
    return None

async def sniping_loop(chat_id, service, countries):
    while active_loops.get(chat_id, False):
        for country in countries:
            if not active_loops.get(chat_id, False):
                break
            url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={service}&country={country}"
            res = requests.get(url).text
            if "ACCESS_NUMBER" in res:
                parts = res.split(":")
                activation_id = parts[1]
                number = parts[2]
                await bot.send_message(chat_id, f"✅ [{country}] رقم: {number}
🆔 ID: {activation_id}")
                code = get_sms_code(activation_id)
                if code:
                    await bot.send_message(chat_id, f"📩 كود التفعيل: {code}")
                else:
                    await bot.send_message(chat_id, "⚠️ لم يتم استلام الكود.")
            await asyncio.sleep(3)
        await asyncio.sleep(2)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_config[message.chat.id] = {"countries": []}
    await message.answer("🌍 اختر الدول (يمكنك اختيار أكثر من دولة):",
                         reply_markup=get_keyboard(COUNTRIES, "country", multi=True))

@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    cid = call.message.chat.id
    data = call.data

    if data.startswith("country:"):
        code = data.split(":")[1]
        selected = user_config[cid]["countries"]
        if code in selected:
            selected.remove(code)
        else:
            selected.append(code)
        await call.message.edit_reply_markup(
            reply_markup=get_keyboard(COUNTRIES, "country", multi=True, selected=selected))

    elif data == "confirm":
        await call.message.answer("🔧 اختر الخدمة:", reply_markup=get_keyboard(SERVICES, "service"))

    elif data.startswith("service:"):
        service = data.split(":")[1]
        user_config[cid]["service"] = service
        await call.message.answer("🚀 تم الحفظ! جاري الصيد...
🛑 أرسل /stop لإيقاف العملية.")
        active_loops[cid] = True
        asyncio.create_task(sniping_loop(cid, service, user_config[cid]["countries"]))

@dp.message(lambda message: message.text == "/stop")
async def stop_cmd(message: types.Message):
    cid = message.chat.id
    active_loops[cid] = False
    await message.answer("🛑 تم إيقاف الصيد بنجاح.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())