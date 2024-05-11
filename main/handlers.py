import os
import json
import aiofiles

from datetime import (
    datetime, 
    timezone,
    timedelta,
)

from aiogram import (
    Router, 
    F, 
    types, 
)
from aiogram.fsm.context import (
    FSMContext,
)
from aiogram.filters import (
    Command, 
)

from main import (
    utils as main_utils,
    keyboards as main_keyboards,
)
from bot import (
    bot,
    MainStatesGroup,
)

# 👋📖📝🛰️🛸👨‍🔬👩‍🏫

main_router = Router(name='main')


@main_router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    '''
        Вход в бота
        Если пользователь не зарегистрирован то переводит на регистрацию
        Иначе основное меню
    '''
    await state.clear()

    from_user_id = message.from_user.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
    if user_is_allowed:
        user_data = {}

        if not os.path.exists('profiles'):
            os.mkdir('profiles')

        file_path = f'profiles/{from_user_id}.js'
        
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, mode='r') as f:
                user_data = json.loads(await f.read())
                await state.update_data(user_data=user_data)

        else:
            start_of_use = int(datetime.now().timestamp())
            async with aiofiles.open(file_path, mode='w') as f:
                await f.write(json.dumps({'start_of_use': start_of_use}))

        training_status = user_data.get('training_status', False)

        text = "👋 Добро пожаловать в <b>Нейро-тест бота</b>\n\nОн преднозначен для обучения 👩‍🏫 и проверки знаний 📝."

        if  training_status == "finished":
            text += "\n\nВы уже закончили обучение можете задавать вопросы нейро-консультанту 👨‍🔬"
        else:
            text += "\n\nПосле прохождения обучения вам будет доступен нейро-консультант 👨‍🔬, он поможет вам в вопросах по теме."

        new_message = await message.answer(
            text,
            parse_mode='html',
            reply_markup=main_keyboards.get_menu_keyboard(training_status)    
        )

        await main_utils.append_value_state_data(state, 'previous_messages', [new_message.message_id])

        await bot.set_my_commands(
            commands=[types.BotCommand(command='/menu', description='Меню')],
            scope=types.BotCommandScopeAllPrivateChats(),
            # scope=types.BotCommandScopeDefault(),
        )
        # await main_utils.delete_previous_messages(bot, message, state)
        # await main_utils.try_message_delete(message)      


@main_router.message(Command("menu"))
async def start(message: types.Message, state: FSMContext):
    '''
        Выходит в меню
    '''
    await main_utils.try_message_delete(message)
    await main_utils.delete_previous_messages(bot, message, state)
    await state.clear()

    new_message = await message.answer(
        "🚧 Меню пока не работает, используйте /start",
        parse_mode='html',
    )

    await main_utils.append_value_state_data(state, 'previous_messages', [new_message.message_id])


@main_router.callback_query(
    F.data == 'studying',
)
async def studying(callback: types.CallbackQuery, state: FSMContext):
    '''
        Запускает обучение
    '''
    # Проверяем может ли пользователь использовать бота
    from_user_id = callback.message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(callback.message, from_user_id)
  
    if user_is_allowed:
        await state.set_state(MainStatesGroup.studying)   

        last_stage = await main_utils.get_last_stage(state)

        stage_line_numbers = main_utils.get_stage_line_numbers_list()

        stage_content = main_utils.get_stage_content_by_number(last_stage)
        # print('stage_content', stage_content)  
        await main_utils.delete_previous_messages(bot, callback.message, state)

        await callback.answer(
            text=str(
                '🔎 Изучите материал.'
                '\n📝 За тем пройдите тестирование'
            ),
            show_alert=True,
        )

        message_data = {
            'text': stage_content,    
            'chat_id': from_user_id,
            'parse_mode': 'html',
            'reply_markup': main_keyboards.get_studying_keyboard(),
        }  
        message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

        if is_sent:
            await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])  


@main_router.callback_query(
    F.data == 'go_to_testing',
)
async def studying(callback: types.CallbackQuery, state: FSMContext):
    '''
        Запускает тестирование
    '''
    # Проверяем может ли пользователь использовать бота
    state_data = await state.get_data()
    from_user_id = callback.message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(callback.message, from_user_id)
  
    if user_is_allowed:
        await state.set_state(MainStatesGroup.testing)   

        last_stage = await main_utils.get_last_stage(state)        
        last_question_num = state_data.get('last_question_num', 0)

        question_data = await main_utils.get_question_data(last_stage, last_question_num) 

        # print('question_data', question_data)




        stage_line_numbers = main_utils.get_stage_line_numbers_list()

        stage_content = main_utils.get_stage_content_by_number(last_stage)
        # print('stage_content', stage_content)  
        await main_utils.delete_previous_messages(bot, callback.message, state)

        await callback.answer(
            text=str(
                '🔎 Изучите материал.'
                '📝 За тем пройдите тестирование'
            ),
            show_alert=True,
        )

        message_data = {
            'text': stage_content,    
            'chat_id': from_user_id,
            'parse_mode': 'html',
            'reply_markup': main_keyboards.get_studying_keyboard(),
        }  
        message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

        if is_sent:
            await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 
