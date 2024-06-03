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
    exceptions,
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
    general_rate_slug,
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

    """
        Нужно попытаться получить файл с id юзера
        Если он есть по востановить сессию
        если нет то спросить профиль, пароль, фио
        после регистрации начать обучение
    """

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
        registration_status = user_data.get('registration_status', False)

        if not registration_status:            
            await state.set_state(MainStatesGroup.registration) 
            await registration(message, state)
            return
        


        await state.set_state(MainStatesGroup.studying)   
        state_data = await state.get_data()
        user_data = state_data.get('user_data')

        text = "👋 Добро пожаловать в <b>Нейро-тест бота</b>\n\nОн преднозначен для обучения 👩‍🏫 и проверки знаний 📝."

        if  training_status == "finished":
            text += "\n\nВы уже закончили обучение можете задавать вопросы нейро-консультанту 👨‍🔬"
        else:

            completed_course_slugs_list = user_data.get('completed_course_slugs_list', [])

            if len(completed_course_slugs_list) == 0:
                course_slug = general_rate_slug

            if len(completed_course_slugs_list) == 1:
                course_slug = user_data.get('departament')        

            await state.update_data(course_slug=course_slug)
            stage_num = 1
            await state.update_data(stage_num=stage_num)
            stage_slug = main_utils.get_stage_slug(course_slug, stage_num)

            text += "\n\nПосле прохождения обучения вам будет доступен нейро-консультант 👨‍🔬, он поможет вам в вопросах по теме."

        new_message = await message.answer(
            text,
            parse_mode='html',
            reply_markup=main_keyboards.get_menu_keyboard(course_slug, stage_slug, training_status)    
        )

        await main_utils.append_value_state_data(state, 'previous_messages', [new_message.message_id])

        await bot.set_my_commands(
            commands=[types.BotCommand(command='/menu', description='Меню')],
            scope=types.BotCommandScopeAllPrivateChats(),
            # scope=types.BotCommandScopeDefault(),
        )
        # await main_utils.delete_previous_messages(bot, message, state)
        # await main_utils.try_message_delete(message)      


@main_router.message(
    MainStatesGroup.registration,       
)
async def registration(message: types.Message, state: FSMContext):
    '''
        Обрабатывает регистрацию
    '''
    status = True
    from_user_id = message.chat.id
    state_data = await state.get_data()
    # print("state_data", state_data)
    registration_stage = state_data.get('registration_stage', 0)
    departament = state_data.get('departament')
    
    if registration_stage + 1 > 3:
        user_data = state_data.get('user_data')
        user_data['registration_status'] = True
        await state.update_data(user_data=user_data)
        await main_utils.save_profile(from_user_id, user_data)
        await state.set_state(MainStatesGroup.studying) 
        await start(message, state)
        return

    text = main_keyboards.REGISTRATION_DATA[registration_stage].get('text')
    reply_markup = main_keyboards.get_registration_keyboard(registration_stage)

    if registration_stage == 2:
        departament_paswords = []
        for item in main_keyboards.PASSWORD_DATA:
            if item["departament"] == departament:
                departament_paswords = item.get("passwords", [])

        if message.text not in departament_paswords:
            text = "Пароль не верен"
            status = False
            reply_markup = None

    await main_utils.delete_previous_messages(bot, message, state)

    if status:
        await state.update_data(registration_stage=registration_stage + 1)

    message_data = {
        'text': text,    
        'chat_id': from_user_id,
        'parse_mode': 'html',
        'reply_markup': reply_markup,
    }  
    message, is_sent = await main_utils.send_message(bot, message_data)

    if is_sent:
        await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])
    


@main_router.callback_query(
    MainStatesGroup.registration,
)
async def callback_registration(callback: types.CallbackQuery, state: FSMContext):
    '''
        Принимает кнопки регистрации
    '''
    departament_slug = callback.data
    state_data = await state.get_data()

    registration_stage = state_data.get('registration_stage', 0)
    if registration_stage == 1:
        await state.update_data(departament=departament_slug)
        state_data = await state.get_data()

    await registration(callback.message, state)


@main_router.message(Command("menu"))
async def menu(message: types.Message, state: FSMContext):
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



@main_router.message(
    F.web_app_data.data,
)
async def web_app(message: types.Message, state: FSMContext):
    web_app_data = message.web_app_data    
    # if web_app_data.data == 'done':
    print("web_app_data.data", web_app_data.data)

    await state.set_state(MainStatesGroup.testing)   
    await testing(message, state)


"""
    Нужно ублать studying
    Вместо этого, все первые переменные должны выставляться на старте (или меню)
    Так же нужно изменить то как тестирование работает(частично поменялась структура, а так же появились курсы)
"""


async def testing(message: types.Message, state: FSMContext):
    '''
        Запускает тестирование
    '''
    # Проверяем может ли пользователь использовать бота
    print("testing")
    from_user_id = message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
  
    if user_is_allowed:
        await state.set_state(MainStatesGroup.testing)   
        state_data = await state.get_data()
        user_data = state_data.get('user_data')
        course_slug = state_data.get('course_slug')
        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num', 1)    
        if question_num == 1:
            await state.update_data(question_num=question_num)           

        question_data = await main_utils.get_question_data(course_slug, stage_num - 1 , question_num - 1) 

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
    await state.update_data(
        last_callback_id=callback.id
    )    
    await testing(callback.message, state)


@main_router.callback_query(
    MainStatesGroup.testing,
    F.data.split('__')[0] == 'answer',
)
async def verification(callback: types.CallbackQuery, state: FSMContext):
    '''
        Проверяет тестирование
    '''
    # Проверяем может ли пользователь использовать бота
    print('verification')
    state_data = await state.update_data(
        last_callback_id=callback.id
    )
    from_user_id = callback.message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(callback.message, from_user_id)
  
    if user_is_allowed:
        answer_index = int(callback.data.split('__')[1])

        course_slug = state_data.get('course_slug')
        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num')     


        question_data = await main_utils.get_question_data(course_slug, stage_num - 1, question_num - 1) 

        is_correct_answer = False
        answer = question_data.get('answers')[answer_index]
        if question_data.get('correct_answer') == answer:
            is_correct_answer = True

        user_data: dict = state_data.get("user_data")
        studying_history: dict = user_data.get('studying_history', {})
        course_history: list = studying_history.get(course_slug, [])

        stage_history = []
        if studying_history:
            try:
                stage_history: list = course_history.pop(stage_num - 1)
            except IndexError:
                pass
        
        stage_history.append({'is_correct_answer': is_correct_answer})
        course_history.insert(stage_num - 1, stage_history)

        studying_history[course_slug] = course_history
        print('studying_history', studying_history)

        user_data['studying_history'] = studying_history
        await state.update_data(user_data=user_data)
        await main_utils.save_profile(from_user_id, user_data)

        stage_questions_data = await main_utils.get_stage_questions_data(course_slug, stage_num - 1) 

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
    # Проверяем может ли пользователь использовать бота
    # print('verification')
    from_user_id = message.chat.id
    user_is_allowed = await main_utils.user_is_allowed(message, from_user_id)
  
    if user_is_allowed:
        answer = message.text
        state_data = await state.get_data()
        stage_num = state_data.get('stage_num')
        question_num = state_data.get('question_num')     
        course_slug = state_data.get('course_slug')     

        question_data = await main_utils.get_question_data(course_slug, stage_num - 1, question_num - 1) 

        is_correct_answer = await interface.verification_correct_answer(question_data, answer)

        user_data: dict = state_data.get("user_data")
        studying_history: dict = user_data.get('studying_history', {})
        course_history: list = studying_history.get(course_slug, [])

        stage_history = []
        if course_history:
            stage_history: list = course_history.pop(stage_num - 1)
        
        stage_history.append({'is_correct_answer': is_correct_answer})
        course_history.insert(stage_num - 1, stage_history)
        studying_history[course_slug] = course_history
        # print('studying_history', studying_history)

        user_data['studying_history'] = studying_history
        await state.update_data(user_data=user_data)
        await main_utils.save_profile(from_user_id, user_data)
        stage_questions_data = await main_utils.get_stage_questions_data(course_slug, stage_num - 1) 

        if question_num < len(stage_questions_data):
            await state.update_data(
                question_num=question_num + 1
            )
            await testing(message, state) 
        else:
            questions_data = interface.get_questions_data()
            if stage_num <= len(questions_data):
                await state.update_data(
                    stage_num=stage_num + 1,
                    question_num=1,
                )
                text = f"Тема завершена"  
                reply_markup = main_keyboards.get_menu_keyboard(course_slug , 1, 'kkk')

            else:
                text = str(
                    f"\n\nВы набрали ... балов"
                    # f"\n\nВы набрали {main_utils.get_points_count(studying_history)} балов"
                )
                completed_course_slugs_list:list = user_data.get('completed_course_slugs_list', [])
                completed_course_slugs_list.append(course_slug)
                await state.update_data(
                    completed_course_slugs_list=completed_course_slugs_list
                )

                if len(completed_course_slugs_list) < 2:
                    reply_markup = main_keyboards.get_question_keyboard(question_data.get('answers'))
                    text = f"Курс завершен" + text
                else:
                    reply_markup = main_keyboards.get_menu_keyboard(user_data.get('departament') , 1, 'kkk')
                    text = f"Обучение завершено" + text


            await main_utils.delete_previous_messages(bot, message, state)
            message_data = {
                'text': text,    
                'chat_id': from_user_id,
                'parse_mode': 'html',
                'reply_markup': reply_markup,
            }  
            message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

            if is_sent:
                await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])                 