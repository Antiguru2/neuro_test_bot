import asyncio

from typing import Optional

from aiogram import (
    Bot,
    types, 
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)



async def send_then_delete(
    bot: Bot,
    message: types.Message, 
    text: str = 'Временное сообщение', 
    seconds=30,
):
    new_message = await bot.send_message(message.chat.id, text, parse_mode="HTML")
    await asyncio.sleep(seconds)  
    await new_message.delete()


def get_button_exit(title: str = '🔙  Выйти в меню'):
    '''
        Возвращает кнопку выхода в меню
    '''
    button_exit = types.InlineKeyboardButton(
        text=title, callback_data=f"exit"
    )
    return button_exit


def get_button_back():
    '''
        Возвращает кнопку назад
    '''
    button_back = types.InlineKeyboardButton(
        text="Назад", callback_data=f"back"
    )
    return button_back


def get_web_app():
    '''
        Возвращает кнопку назад
    '''
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text='web_app', 
        web_app=types.WebAppInfo(
            url='https://basestore.site/',
        )
    ))
    return builder.as_markup()


def get_menu_keyboard(training_status):
    '''
        Возвращает первую клавиатуру
    '''
    builder = InlineKeyboardBuilder()
    if training_status != 'finished':
        if not training_status:
            text = "Приступить к обучению 👩‍🏫"
        else:
            text = "Продолжить обучение 👩‍🏫"

        builder.row(types.InlineKeyboardButton(
            text=text, callback_data=f"studying",
        ))
    return builder.as_markup()


def get_studying_keyboard():
    '''
        Возвращает клавиатуру перевода на тестирование
    '''
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
            text='Перейти к тестированию 📝', callback_data=f"go_to_testing",
    ))
    return builder.as_markup()


def get_question_keyboard(answers: list) -> Optional[types.InlineKeyboardMarkup]:
    '''
        Возвращает первую клавиатуру
    '''
    builder = InlineKeyboardBuilder()
    if answers:
        builder.row(
            types.InlineKeyboardButton(
            text=answers[0], callback_data=f"answer__0",
            ), types.InlineKeyboardButton(
            text=answers[1], callback_data=f"answer__1",
            )
        )
        builder.row(
            types.InlineKeyboardButton(
            text=answers[2], callback_data=f"answer__2",
            ), types.InlineKeyboardButton(
            text=answers[3], callback_data=f"answer__3",
            )
        )        
    return builder.as_markup()