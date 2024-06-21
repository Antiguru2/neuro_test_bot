import os
import re
import json
import requests
import aiofiles

from dotenv import load_dotenv
from pprint import pprint

from aiogram.fsm.context import FSMContext
from aiogram import (
    Bot,
    exceptions,
    types,
)

from interfaces import test_interface as interface

load_dotenv()

allowed_users_list = os.getenv('ALLOUWED_USERS', '').split(",")

TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN = os.getenv('TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN')
CHANNEL_FOR_SEND_ERRORS_ID = os.getenv('CHANNEL_FOR_SEND_ERRORS_ID')  
WEB_APP_PATH = os.getenv('WEB_APP_PATH')  


async def try_message_delete(message: types.Message):
    '''
        Удаляет сообщение
    '''
    try:
        await message.chat.delete_message(message.message_id)
    except exceptions.TelegramBadRequest:
        pass   


async def delete_previous_messages(
    bot: Bot,  
    message: types.Message, 
    state: FSMContext
):
    '''
        Удаляет сообщение
    '''
    state_data = await state.get_data()
    previous_messages = state_data.get('previous_messages')

    if previous_messages:
        try:
            await bot.delete_messages(
                chat_id=message.chat.id,
                message_ids=previous_messages,
            )   
        except exceptions.TelegramBadRequest:
            pass


async def edit_message_or_send(
    bot: Bot, 
    state: FSMContext, 
    message_data: dict = {}, 
):
    '''
        Пытается изменить последнее сообщение 
        иначе создает новое
    '''
    is_send = None
    is_edit = None
    message = None

    state_data = await state.get_data()
    previous_messages_ids_list = state_data.get('previous_messages', [])

    if previous_messages_ids_list:
        message_data['message_id'] = previous_messages_ids_list[-1]

        message, is_edit = await edit_message(bot, message_data)

        if is_edit:
            is_send = False

    if is_edit != True:
        message, is_send = await send_message(bot, message_data)

    return message, is_send


async def send_message(
    bot: Bot, 
    message_data: dict = {}, 
):
    '''
        Отправляет сообщение
    '''
    message = None
    is_send = False
    if message_data.get('message_id'):
        message_data.pop('message_id')

    if message_data:
        message = await bot.send_message(**message_data)
    if message:
        is_send = True

    return message, is_send
        

async def edit_message(
    bot: Bot, 
    message_data: dict = {}, 
):
    '''
        Пытается отредактировать сообщение
    '''
    message = None
    is_edit = False

    if message_data and message_data.get('text'):
        try:
            message = await bot.edit_message_text(**message_data)
        except exceptions.TelegramBadRequest:
            pass
    
    reply_markup_data = {
        'chat_id': message_data.get('chat_id'),
        'reply_markup': message_data.get('reply_markup', types.InlineKeyboardMarkup(inline_keyboard=[])),
        'message_id': message_data.get('message_id'),            
    }
    try:
        message = await bot.edit_message_reply_markup(**reply_markup_data)
    except exceptions.TelegramBadRequest:
        pass    

    if message:
        is_edit = True

    return message, is_edit
  

async def append_value_state_data(state: FSMContext, name: str, values_list: list):
    '''
        Добавляет в список дополнительный элемент
    '''
    state_data = await state.get_data() 
    update_list: list = state_data.get(name, [])
    update_list.extend(values_list)
    await state.update_data({name: update_list})


def get_stage_line_numbers_list() -> list:
    content = interface.get_knowledge_base()

    pattern = r'# (\d+) этап обучения'
    stage_matches = re.finditer(pattern, content)

    stage_line_numbers = [match.start() for match in stage_matches]

    return stage_line_numbers


def get_stage_content_by_number(stage_num: int) -> str:
    content = interface.get_knowledge_base()

    pattern = rf'# {stage_num} этап обучения\n(.*?)(?=\n# |\Z)'
    stage_match = re.search(pattern, content, re.DOTALL)

    if stage_match:
        return stage_match.group(1).strip()
    else:
        return "Этап обучения не найден"
    

async def get_last_stage_num_and_last_question_index(state: FSMContext) -> tuple:
    state_data = await state.get_data()
    user_data = state_data.get('user_data')
    last_stage_num = None
    last_question_index = None
    if user_data:
        studying_history = user_data.get('studying_history')
        if studying_history:
            last_stage_num = len(studying_history) - 1
            last_stage = studying_history[last_stage_num]
            if last_stage:
                last_question_index = len(last_stage) - 1
 
    return last_stage_num, last_question_index


def get_stage_slug(course_slug, stage_num):
    questions_data = interface.get_questions_data()
    courses_data = questions_data[course_slug]
    stage_data = courses_data[stage_num - 1]
    course_slug = stage_data.get('slug')
    return course_slug


def get_total_balls(user_data: dict) -> int:
    total_balls = 0
    studying_history = user_data.get('studying_history', {})
    for course_data in studying_history.values():
        for state_data in course_data:
            for answer_data in state_data:
                answer_data = answer_data.get('is_correct_answer', False)
                if answer_data:
                    total_balls += 1
                    
    return total_balls


def send_message_about_error(error_text, name_sender='None', error_data=None, error_data_is_traceback=False, to_fix=False):
    '''
        Отправляет сообщение в телеграм канал
    '''
    if not TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN or not CHANNEL_FOR_SEND_ERRORS_ID:
        print('Добавьте CHANNEL_FOR_SEND_ERRORS_ID и TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN в настройки приложения')
        return
    
    method = 'sendMessage'
    channel_id = f'-100{ CHANNEL_FOR_SEND_ERRORS_ID }'
    add_error_info = ''
    file_id = None
    text_name = 'text'
    if error_data:
        if error_data_is_traceback:
            # Создаем файл с трейсбеком
            filename = 'traceback.txt'
            with open(filename, 'w') as file:
                file.write('жопа')
            file = {'document': open(filename, 'rb')} 
            text_name = 'caption'
            method = 'sendDocument'                       
        else:
            add_error_info = str(
                f'\n<b>Дополнительная информация:</b>'
                f'\n{error_data}'
            )
    text_for_telegram = str(
        f'\n==============name_sender==============='
        f'\n<b>{name_sender}</b>'
        f'\n===============error_text==============='
        f'\n{error_text}' 
        f'\n========================================'
        f'{add_error_info}'
    )
    data = {'chat_id': channel_id, text_name: text_for_telegram.strip(), 'parse_mode': 'HTML'}
    try:
        url = f'https://api.telegram.org/bot{ TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN }/{method}'
        if text_name == 'caption':
            response = requests.post(url, data, files=file).json()
        else:
            response = requests.post(url, data).json()

        if to_fix:
            message_id = response['result']['message_id']
            # Закрепляем сообщение
            url = f'https://api.telegram.org/bot{TELEGRAM_BOT_FOR_SEND_ERRORS_TOKEN}/pinChatMessage'
            data = {'chat_id': channel_id, 'message_id': message_id, 'disable_notification': True}
            requests.post(url, data)     

    except requests.exceptions.ConnectionError:
        print('equests.exceptions.ConnectionError')
    except:
        print('except')