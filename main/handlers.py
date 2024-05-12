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

from interfaces import test_interface as interface
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

        file_path = f'profiles/{from_user_id}.json'
        
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, mode='r') as f:
                user_data = json.loads(await f.read())
        else:
            start_of_use = int(datetime.now().timestamp())
            async with aiofiles.open(file_path, mode='w') as f:
                user_data = {'start_of_use': start_of_use}
                await f.write(json.dumps(user_data))

        await state.update_data(user_data=user_data)

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


async def studying(message: types.Message, state: FSMContext):
    '''
        Запускает обучение
    '''
    print('studying')
    # Проверяем может ли пользователь использовать бота
    from_user_id = message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
  
    if user_is_allowed:
        await state.set_state(MainStatesGroup.studying)   
        state_data = await state.get_data()

        stage_num = state_data.get('stage_num', 1)
        if stage_num == 1:
            await state.update_data(stage_num=stage_num)

        stage_content = main_utils.get_stage_content_by_number(stage_num)

        await main_utils.delete_previous_messages(bot, message, state)

        await bot.answer_callback_query(
            state_data.get('last_callback_id'),
            text=str(
                f'{stage_num} этап'
                '\n🔎 Изучите материал.'
                '\n📝 Затем пройдите тестирование'
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
    F.data == 'studying',
)
async def studying_router(callback: types.CallbackQuery, state: FSMContext):
    '''
        Запускает обучение
    '''
    state_data = await state.update_data(
        last_callback_id=callback.id
    )
    await studying(callback.message, state)


async def testing(message: types.Message, state: FSMContext):
    '''
        Запускает тестирование
    '''
    print('testing')  
    # Проверяем может ли пользователь использовать бота
    from_user_id = message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
  
    if user_is_allowed:
        await state.set_state(MainStatesGroup.testing)   

        state_data = await state.get_data()
        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num', 1)    
        if question_num == 1:
            await state.update_data(question_num=question_num)           

        question_data = await main_utils.get_question_data(stage_num - 1 , question_num - 1) 
        # print('question_data', question_data) 

        await main_utils.delete_previous_messages(bot, message, state)

        message_data = {
            'text': question_data.get('question_text'),    
            'chat_id': from_user_id,
            'parse_mode': 'html',
            'reply_markup': main_keyboards.get_question_keyboard(question_data.get('answers')),
        }  
        message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

        if is_sent:
            await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 


@main_router.callback_query(
    F.data == 'go_to_testing',
)
async def testing_router(callback: types.CallbackQuery, state: FSMContext):
    '''
        Запускает тестирование
    '''
    await testing(callback.message, state)


@main_router.callback_query(
    MainStatesGroup.testing,
    F.data.split('__')[0] == 'answer',
)
async def verification(callback: types.CallbackQuery, state: FSMContext):
    '''
        Проверяет тестирование
    '''
    print('verification')  
    # Проверяем может ли пользователь использовать бота
    state_data = await state.update_data(
        last_callback_id=callback.id
    )
    from_user_id = callback.message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(callback.message, from_user_id)
  
    if user_is_allowed:
        answer_index = int(callback.data.split('__')[1])

        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num')     


        question_data = await main_utils.get_question_data(stage_num - 1, question_num - 1) 

        is_correct_answer = False
        answer = question_data.get('answers')[answer_index]
        if question_data.get('correct_answer') == answer:
            is_correct_answer = True

        user_data: dict = state_data.get("user_data")
        studying_history: list = user_data.get('studying_history', [])
        stage_history = []
        print('studying_history', studying_history)
        if studying_history:
            try:
                stage_history: list = studying_history.pop(stage_num - 1)
            except IndexError:
                pass
        
        stage_history.append({'is_correct_answer': is_correct_answer})

        studying_history.insert(stage_num - 1, stage_history)

        user_data['studying_history'] = studying_history
        await state.update_data(user_data=user_data)
        await main_utils.save_profile(from_user_id, user_data)
        stage_questions_data = await main_utils.get_stage_questions_data(stage_num - 1) 

        if question_num < len(stage_questions_data):
            state_data = await state.update_data(
                question_num=question_num + 1
            )
            await testing(callback.message, state)


@main_router.message(
    MainStatesGroup.testing,
)
async def verification(message: types.Message, state: FSMContext):
    '''
        Проверяет тестирование
    '''
    print('verification')  
    # Проверяем может ли пользователь использовать бота
    from_user_id = message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
  
    if user_is_allowed:
        answer = message.text
        state_data = await state.get_data()
        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num')     

        question_data = await main_utils.get_question_data(stage_num - 1, question_num - 1) 

        is_correct_answer = await interface.verification_correct_answer(question_data, answer)

        user_data: dict = state_data.get("user_data")
        studying_history: list = user_data.get('studying_history', [])
        stage_history = []
        if studying_history:
            stage_history: list = studying_history.pop(stage_num - 1)
        
        stage_history.append({'is_correct_answer': is_correct_answer})

        studying_history.insert(stage_num - 1, stage_history)

        user_data['studying_history'] = studying_history
        await state.update_data(user_data=user_data)
        await main_utils.save_profile(from_user_id, user_data)
        stage_questions_data = await main_utils.get_stage_questions_data(stage_num - 1) 

        if question_num < len(stage_questions_data):
            await state.update_data(
                question_num=question_num + 1
            )
            await testing(message, state) 
        else:
            print('stage_num', stage_num)
            print('len(studying_history)', len(studying_history))
            questions_data = interface.get_questions_data()
            if stage_num < len(questions_data):
                await state.update_data(
                    stage_num=stage_num + 1,
                    question_num=1,
                )
                await studying(message, state)        

            else:
                await main_utils.delete_previous_messages(bot, message, state)

                message_data = {
                    'text': str(
                        f"Обучение завершено"
                        f"\nВы набрали {main_utils.get_points_count(studying_history)} балов"
                    ),    
                    'chat_id': from_user_id,
                    'parse_mode': 'html',
                    'reply_markup': main_keyboards.get_question_keyboard(question_data.get('answers')),
                }  
                message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

                if is_sent:
                    await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])                 