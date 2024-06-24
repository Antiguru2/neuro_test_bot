import os
import asyncio

from dotenv import load_dotenv
from typing import Optional

from aiogram import (
    Bot,
    types, 
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)

load_dotenv()

WEB_APP_PATH = os.getenv('WEB_APP_PATH') 


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


def get_web_app_button(url: str ='https://basestore.site/', text: str = 'web_app'):
    '''
        Возвращает кнопку web_app
    '''
    button = types.InlineKeyboardButton(
        text=text, 
        web_app=types.WebAppInfo(
            url=url,
        ),
    )
    return button


def get_web_app_keyboard(url: str ='https://basestore.site/', text: str = 'web_app'):
    '''
        Возвращает клавиатуру web_app
    '''
    builder = InlineKeyboardBuilder()
    builder.row(get_web_app_button(url, text))
    return builder.as_markup()


def get_menu_keyboard(course_slug, stage_slug, is_trained):
    '''
        Возвращает первую клавиатуру
    '''
    builder = InlineKeyboardBuilder()

    if not is_trained:
        url = f"{WEB_APP_PATH}{course_slug}/{stage_slug}/"
        text = "Изучить материал 👩‍🏫"

        builder.row(get_web_app_button(url, text))

        builder.row(types.InlineKeyboardButton(
                text='Перейти к тестированию 📝', callback_data=f"go_to_testing",
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

REGISTRATION_DATA = [
    {   
        "slug": "departament",
        "text": "Выберите ваш отдел 🏢",
        "buttons": [
            {
                "name": "Бугартерия 🧮",
                "slug": "accounting",
            },{
                "name": "Менеджмент 📊",
                "slug": "management",
            },{
                "name": "Оптовый отдел 📦",
                "slug": "wholesaler",
            },
        ]
    },
    {   
        "slug": "password",
        "text": "Введите пароль 🔑",
        "buttons": []
    },
    {   
        "slug": "full_name",
        "text": "Введите ФИО 📇",
        "buttons": []
    },
]

PASSWORD_DATA = [
    { 
        "departament": "accounting",
        "passwords": [
            "1111"
        ]
    },{ 
        "departament": "management",
        "passwords": [
            "2222"
        ]
    },{ 
        "departament": "wholesaler",
        "passwords": [
            "3333"
        ]
    },
]



def get_registration_keyboard(registration_stage: int) -> Optional[types.InlineKeyboardMarkup]:
    '''
        Возвращает клавиатуру для регистрации
    '''
    builder = InlineKeyboardBuilder()
    reg_stage_data = REGISTRATION_DATA[registration_stage]

    buttons = reg_stage_data.get('buttons')
    if buttons:
        for button in buttons:
            text = button.get('name')
            slug = button.get('slug')

            builder.row(
                types.InlineKeyboardButton(
                    text=text, callback_data=slug,
                ),
            )  
        return builder.as_markup()
    else:
        return None