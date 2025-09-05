from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import asyncio
from dotenv import load_dotenv
import os
from .keyboards import *
from .db.db import db
from ..parser.parser import get_product_info_4_bot

import random

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def price_monitoring():
    """
    Асинхронная задача для периодической проверки цен на товары.
    """
    while True:
        print("Запуск проверки цен...")
        products_to_check = db.get_all_products_for_monitoring()
        for product_id, article, size, name in products_to_check:
            # Небольшая задержка, чтобы не спамить API
            await asyncio.sleep(1)
            product_data = get_product_info_4_bot(article, size if size != "-1" else None)

            if product_data and product_data.get('price') is not None:
                new_price = product_data['price']
                price_change = db.update_product_price(product_id, new_price)

                if price_change:
                    old_price, current_price = price_change
                    users_to_notify = db.get_users_for_product(product_id)
                    for user_id in users_to_notify:
                        try:
                            size_text = f" (размер: {size})" if size != "-1" else ""
                            await bot.send_message(user_id, f"Цена на товар '{name}'{size_text} изменилась!\nСтарая цена: {old_price} ₽\nНовая цена: {current_price} ₽")
                        except Exception as e:
                            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        
        await asyncio.sleep(random.uniform(5.5 * 3600, 6.5 * 3600)) 

@dp.message(CommandStart())
async def start_command(message: types.Message):
    db.add_user(message.from_user.id)
    await message.answer(
        "Привет, я бот который умеет отслеживать изминения цены товаров на сайте wildberries!",
        reply_markup=get_start_keyboard()
    )

@dp.message(lambda Message: Message.text == "Список товаров")
async def get_products_list(message: types.Message):
    pr_list = db.get_products_list(message.from_user.id)

    if not pr_list:
        await message.answer("Список товаров пуст", reply_markup=get_start_keyboard())
        return
    await message.answer("Список товаров:", reply_markup=get_products_list_keyboard(pr_list))

@dp.message(lambda Message: Message.text == "Добавить товар")
async def add_product(message: types.Message):
    db.set_user_status(message.from_user.id, "waiting_for_art")
    await message.answer("Введите артикул товара:", reply_markup=cancel_add_product_keyboard())


@dp.message()
async def main_message_handler(message: types.Message):
    user_id = message.from_user.id
    if db.get_user_status(user_id) == "waiting_for_art":
        article = message.text
        if not article.isdigit():
            article = article.split("/")
            for c in article:
                if not(c == "https:" or "www" in c or "ru" in c or "." in c or c == "" or c == "catalog"): 
                    article = c
                    break
            if not article.isdigit() or not article:
                await message.answer("Кажется артикул неверный. Попробуйте еще раз")
            

        await message.answer("Ищу товар...")
        product_data = get_product_info_4_bot(article)
        print(product_data)
        if product_data.get("Except") == "need_more_details":
            await message.answer("Выберете размер товара:", reply_markup=get_size_keyboard(product_data["sizeOrigNames"], article))
            return
        elif product_data.get("Except") == 0:
            # print(product_data)
            db.add_product(
                user_id=user_id,
                article=int(article),
                name=product_data['name'],
                price=product_data['price'],
                size="-1"
            )
            db.set_user_status(user_id, "active")
            await message.answer(f"Товар '{product_data['name']}' успешно добавлен!", reply_markup=get_start_keyboard())
        else:
            await message.answer("Товар с таким артикулом не найден. Попробуйте еще раз.", reply_markup=cancel_add_product_keyboard())

@dp.callback_query(lambda c: c.data.startswith("size_"))
async def add_prod_with_size(callback: types.CallbackQuery):
    print(callback.data)
    _, size, article = callback.data.split("_", 2)
    product_data = get_product_info_4_bot(article, size)
    if product_data and product_data.get("Except") == "size is not available":
        await callback.message.answer("Размер не найден. Попробуйте еще раз.", reply_markup=cancel_add_product_keyboard())
        return
    # Проверяем, что товар найден и у него есть цена
    if product_data and product_data.get('price') is not None:
        db.add_product(
            user_id=callback.from_user.id,
            article=int(article),
            name=product_data['name'],
            price=product_data['price'],
            # Используем размер из callback'а, который мы уже получили
            size=size,
        )
        db.set_user_status(callback.from_user.id, "active")
        await callback.message.answer("Товар успешно добавлен!", reply_markup=get_start_keyboard())
    else:
        await callback.message.answer("Что-то пошло не так, попробуйте еще раз.", reply_markup=cancel_add_product_keyboard())


@dp.callback_query(lambda c: c.data.startswith("product_"))
async def get_product_info(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product_info = db.get_product_info(product_id)
    # product_info += "\nСсылка: https://www.wildberries.ru/catalog/" + str(product_id) + "/detail.aspx"
    # print(product_info)
    if(product_info):
        user_id = callback.from_user.id
        await callback.message.answer(product_info, reply_markup=get_product_actions_inline_keyboard(user_id, product_id))


@dp.callback_query(lambda c: c.data == "cancel_add_product")
async def cancel_add_product(callback: types.CallbackQuery):
    db.set_user_status(callback.from_user.id, "active")
    await callback.message.answer("Добавление отменено", reply_markup=get_start_keyboard())

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_product_tracking(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    db.delete_user_product(user_id, product_id)

    await callback.answer("Товар удален из отслеживания.")

    # Обновляем сообщение со списком товаров
    pr_list = db.get_products_list(user_id)
    if not pr_list:
        await callback.message.edit_text("Список отслеживаемых товаров пуст.", reply_markup=None)
    else:
        await callback.message.edit_text("Товар удален. Ваш обновленный список:", reply_markup=get_products_list_keyboard(pr_list))


@dp.callback_query(lambda c: c.data.startswith("toggle_notify_"))
async def toggle_product_notification(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    new_status = db.toggle_notifications(user_id, product_id)

    if new_status is not None:
        status_text = "включены" if new_status else "отключены"
        await callback.answer(f"Уведомления {status_text}.")
        # Обновляем клавиатуру в существующем сообщении
        await callback.message.edit_reply_markup(reply_markup=get_product_actions_inline_keyboard(user_id, product_id))

@dp.callback_query(lambda c: c.data == "back")
async def back_to_list(callback: types.CallbackQuery):
    await callback.message.answer("Список товаров:", reply_markup=get_products_list_keyboard(db.get_products_list(callback.from_user.id)))



async def main():
    asyncio.create_task(price_monitoring())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
