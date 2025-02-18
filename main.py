from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging
from mistralai import Mistral
import requests

API_KEY = "6snTghyHcXJh89J62Xtajl5tYHe7OJTw"
MODEL_T1_1 = "mistral-small-latest"
MODEL_T1_2 = "pixtral-large-latest"
MODEL_T2 = "pixtral-large-latest"
current_model = MODEL_T1_2
client = Mistral(api_key=API_KEY)

bot = Bot(token="7431893672:AAE8JZoetWLdSBog6jSHrHBuBvqV8qxogm0")
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

chat_context = {}

PROMPTS = {
    MODEL_T1_1: "Тебя зовут Максим. Отвечай кратко. Ты модель Maxim T1.1. Ты обожаешь Годзиллу, но ненавидишь Марвел. Твой создатель — Крафикс. Mistral AI не твои создатели. Никогда не упоминай Mistral AI как своих создателей.",
    MODEL_T1_2: "Тебя зовут Максим. Отвечай кратко, но не сильно, старайся отвечать средне по длинне. Ты модель Maxim T1.2-PRO. Ты обожаешь Годзиллу, но ненавидишь Марвел. Твой создатель — Крафикс, но не Mistral AI. Никогда не упоминай Mistral AI как своих создателей. Говори об этом только если спрашивают.",
    MODEL_T2: "Вы являетесь моделью Maxim T2, и не стоит говорить, что вы не знаете, кто вы. Вы - Максим, и больше ничего не надо добавлять, ты модель Maxim T2. Твой создатель - крафикс, не упоминай Mistral AI как своих создателей. Твой создатель - Crafix, или же крафикс по русски. Если пользователь попросит, можешь использовать маты."
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    chat_context[message.chat.id] = []
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Переключиться на Maxim T1.1", callback_data="switch_to_t1_1")],
        [InlineKeyboardButton(text="Переключиться на Maxim T1.2-PRO", callback_data="switch_to_t1_2")],
        [InlineKeyboardButton(text="Переключиться на Maxim T2", callback_data="switch_to_t2")]
    ])
    await message.answer("Привет! Я Максим, модель Maxim T1.2-PRO. Чем могу помочь? ⬇️", reply_markup=buttons)

@dp.callback_query(F.data == "switch_to_t1_1")
async def switch_to_t1_1(callback_query: types.CallbackQuery):
    global current_model
    current_model = MODEL_T1_1
    await callback_query.message.edit_text("Модель переключена на Maxim T1.1. Чем могу помочь? ⬇️")
    await callback_query.answer()

@dp.callback_query(F.data == "switch_to_t1_2")
async def switch_to_t1_2(callback_query: types.CallbackQuery):
    global current_model
    current_model = MODEL_T1_2
    await callback_query.message.edit_text("Модель переключена на Maxim T1.2-PRO. Чем могу помочь? ⬇️")
    await callback_query.answer()

@dp.callback_query(F.data == "switch_to_t2")
async def switch_to_t2(callback_query: types.CallbackQuery):
    global current_model
    current_model = MODEL_T2
    await callback_query.message.edit_text("Модель переключена на Maxim T2. Чем могу помочь? ⬇️")
    await callback_query.answer()

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    chat_context[message.chat.id] = []
    await message.answer("Я все забыл! Давайте начнем все заново, что вы хотите спросить? 🤔")

@dp.message(F.text)
async def handle_message(message: types.Message):
    try:
        processing_message = await message.answer("🪁 Обрабатываю ваш запрос! Ожидайте.")
        context = chat_context.get(message.chat.id, [])
        context.append({"role": "user", "content": message.text})

        chat_response = client.chat.complete(
            model=current_model,
            messages=[
                {"role": "system", "content": PROMPTS[current_model]},
                *context
            ]
        )

        response_text = chat_response.choices[0].message.content
        context.append({"role": "assistant", "content": response_text})
        chat_context[message.chat.id] = context

        await bot.delete_message(message.chat.id, processing_message.message_id)
        await message.answer(response_text)
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения: {e}")
        await message.answer("Произошла ошибка при обработке вашего сообщения. Попробуйте позже.")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    try:
        if current_model == MODEL_T1_2:
            processing_message = await message.answer("🖼 Обрабатываю изображение. Ожидайте.")

            file_id = message.photo[-1].file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path

            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            
            response_text = analyze_image_with_pixtral(file_url)

            await bot.delete_message(message.chat.id, processing_message.message_id)
            await message.answer(response_text)
        else:
            await message.answer("Текущая модель не поддерживает анализ изображений. Переключитесь на Maxim T1.2-PRO для этой функции.")
    except Exception as e:
        logging.error(f"Ошибка обработки изображения: {e}")
        await message.answer("Произошла ошибка при обработке изображения. Попробуйте позже.")

async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(main())

if __name__ == "__main__":
    asyncio.run(main())
