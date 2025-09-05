from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from .db.db import db


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает стартовую Reply-клавиатуру.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text='Список товаров')
    builder.button(text='Добавить товар')
    builder.button(text="Последние изминения цены")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def cancel_add_product_keyboard() -> InlineKeyboardBuilder:

    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data="cancel_add_product")
    builder.adjust(1)
    return builder.as_markup()

def get_size_keyboard(sizes: list[str], article: int | str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in sizes:
        builder.button(text=size, callback_data=f"size_{size}_{article}")
    builder.adjust(2)
    return builder.as_markup()


def get_products_list_keyboard(pr_list: list[tuple]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for pr in pr_list:
        text = f"{pr[1]} ({pr[2]})" if pr[2] != "-1" else pr[1]
        builder.button(text=text, callback_data=f"product_{pr[0]}")
    builder.adjust(1)
    return builder.as_markup()


def get_product_actions_inline_keyboard(user_id: int, product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    notifications_enabled = db.get_notification_status(user_id, product_id)
    if notifications_enabled:
        toggle_text = "Отключить уведомления"
    else:
        toggle_text = "Включить уведомления"

    builder.button(text=toggle_text, callback_data=f"toggle_notify_{product_id}")
    builder.button(text="Удалить из отслеживания", callback_data=f"delete_{product_id}")
    builder.button(text="Назад", callback_data="back")
    builder.adjust(1)
    return builder.as_markup()