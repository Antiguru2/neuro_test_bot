import os
import json
import asyncio
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
from models import (
    Profile,
    Question,
    StudyingHistory,
    CourseHistory,
    StageHistory,
    QuestionHistory,
)
from mixins import (
    TestManager,
)

# 👋📖📝🛰️🛸👨‍🔬👩‍🏫

main_router = Router(name='main')
test_manager = TestManager()


@main_router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    '''
        Вход в бота
        Если пользователь не зарегистрирован то переводит на регистрацию
        Иначе основное меню
    '''
    await main_utils.delete_previous_messages(bot, message, state)
    await state.clear()

    from_user_id = message.from_user.id
    profile = Profile.get(from_user_id)
    await state.update_data(user_data=profile.model_dump())

    if not profile.is_registered:            
        await state.set_state(MainStatesGroup.registration) 
        await registration(message, state)
        return
    
    # Проверка состояния обучения пользователя
    text = "👋 Добро пожаловать в <b>Нейро-тест бота</b>\n\nОн предназначен для обучения 👩‍🏫 и проверки знаний 📝."

    if profile.is_trained:
        await state.set_state(MainStatesGroup.neuro_consult)
        text += "\n\nВы уже закончили обучение можете задавать вопросы нейро-консультанту 👨‍🔬"
        reply_markup = None
    else:
        await state.set_state(MainStatesGroup.studying)   

        course_slug = profile.get_next_course_slug()  

        await state.update_data(course_slug=course_slug)
        await state.update_data(stage_num=1)
        stage_slug = main_utils.get_stage_slug(course_slug, 1)
        reply_markup = main_keyboards.get_menu_keyboard(course_slug, stage_slug, profile.is_trained)

        text += "\n\nПосле прохождения обучения вам будет доступен нейро-консультант 👨‍🔬, он поможет вам в вопросах по теме."

    new_message = await message.answer(
        text,
        parse_mode='html',
        reply_markup=reply_markup,   
    )

    await main_utils.append_value_state_data(state, 'previous_messages', [new_message.message_id])

    await bot.set_my_commands(
        # commands=[types.BotCommand(command='/menu', description='Меню')],
        commands=[types.BotCommand(command='/menu', description='Меню')],
        # scope=types.BotCommandScopeAllPrivateChats(),
        scope=types.BotCommandScopeChat(chat_id=from_user_id),
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
    profile = Profile.get(from_user_id)
    registration_stage = state_data.get('registration_stage', 0)
    departament = state_data.get('departament')
    
    if registration_stage > 2:
        profile.username = message.text
        profile.is_registered = True
        profile.departament = departament

        await state.update_data(user_data=profile.model_dump())
        profile.save()

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

    await state.set_state(MainStatesGroup.testing)   
    await testing(message, state)


async def testing(message: types.Message, state: FSMContext):
    '''
        Функция которая задает вопросы пользователям
    '''
    # print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx testing')
    # Получаем профиль
    from_user_id = message.chat.id
    state_data = await state.get_data()
    profile = Profile.get(from_user_id)
  
    # Переводим пользователя в "тестирование" и 
    # получаем данные о том какой вопрос нужно задавать
    await state.set_state(MainStatesGroup.testing)   
    stage_num = state_data.get('stage_num', 1)
    question_num = state_data.get('question_num', 1)  

    # Обновляем данные о том какой вопрос нужно задавать
    if question_num == 1:
        await state.update_data(question_num=question_num)   

    if stage_num == 1:
        await state.update_data(stage_num=stage_num)   

    course_slug = profile.get_next_course_slug() 
    await state.update_data(course_slug=course_slug)

    # Получаем вопрос
    questions_asked = profile.get_questions_asked(course_slug, stage_num)
    question: Question = test_manager.get_question(
        course_slug, 
        stage_num - 1 , 
        question_num - 1, 
        questions_asked
    ) 

    # Сохраняем данные о том какой вопрос задан
    await state.update_data(questions_ask_num=question.num)  

    # Удаляем все лишнее, формируем данные для сообщения и отправляем его
    await main_utils.delete_previous_messages(bot, message, state)
    message_data = {
        'text': question.text,    
        'chat_id': from_user_id,
        'parse_mode': 'html',
        'reply_markup': main_keyboards.get_question_keyboard(question.answers),
    }  
    message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)
    if is_sent:
        await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 


@main_router.callback_query(
    F.data == 'go_to_testing',
)
async def testing_router(callback: types.CallbackQuery, state: FSMContext):
    '''
        Запускает тестирование по кнопке
    '''
    await testing(callback.message, state)


@main_router.callback_query(
    MainStatesGroup.testing,
    F.data.split('__')[0] == 'answer',
)
async def test_questions_verification(callback: types.CallbackQuery, state: FSMContext):
    '''
        Проверяет ответ на тестовые вопросы
    '''
    # print('________________test_questions_verification')
    # Получаем профиль 
    from_user_id = callback.message.chat.id
    profile = Profile.get(from_user_id)

    await main_utils.delete_previous_messages(bot, callback.message, state)

    # Получаем индекс ответа
    answer_index = int(callback.data.split('__')[1])

    # Получаем данные о том какой вопрос нужно проверять
    state_data = await state.get_data()
    course_slug = state_data.get('course_slug')
    stage_num = state_data.get('stage_num')
    question_num = state_data.get('question_num')     
    questions_ask_num = state_data.get('questions_ask_num')     

    # Получаем вопрос
    question: Question = test_manager.get_question(
        course_slug, 
        stage_num - 1, 
        question_num - 1, 
        questions_ask_index=questions_ask_num - 1
    ) 

    stage_questions_data, questions_count, question_type = test_manager.get_stage_questions_data(course_slug, stage_num - 1, question_num) 
    is_correct, comment = question.get_is_correct_status(answer_index)

    # Если ответ не правильный то скидываем на начало курса
    if not is_correct:
        profile.drop_question_history(
            course_slug, 
            stage_num - 1
        )
        await state.update_data(
            user_data=profile.model_dump(),
            # stage_num=1,
            question_num=1,
        )

        text = '❌ Вы ответили неправильно. Попробуйте еще раз'
        if comment:
            text += f'\n\nℹ️{comment}'
            
        message_data = {
            'text': text,
            'chat_id': from_user_id,
            'parse_mode': 'html',
            'reply_markup': main_keyboards.get_menu_keyboard(
                course_slug=course_slug,
                stage_slug=main_utils.get_stage_slug(course_slug, 1),
                is_trained=profile.is_trained,
            ),
        }  
        message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)
        if is_sent:
            await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])    
        return
    
    question_history = QuestionHistory(
        num=questions_ask_num, 
        type='test_questions',
        is_correct=is_correct,
        question=question.text,
        answer=question.answers[answer_index],
    )

    profile.update_question_history(
        course_slug, 
        stage_num, 
        question_num,
        question_history,
    )


    await state.update_data(user_data=profile.model_dump())

    if question_num <= questions_count:
        state_data = await state.update_data(
            question_num=question_num + 1
        )
        await testing(callback.message, state)


@main_router.message(
    MainStatesGroup.testing,
)
async def open_questions_verification(message: types.Message, state: FSMContext):
    '''
        Проверяет открытые вопросы
    '''
    # print('_____________________open_questions_verification')
    from_user_id = message.chat.id
    state_data = await state.get_data()
    profile: Profile = Profile.get(from_user_id)

    await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 
    reply_markup = None
  
    answer = message.text

    course_slug = state_data.get('course_slug')
    stage_num = state_data.get('stage_num')
    question_num = state_data.get('question_num') 
    questions_ask_num = state_data.get('questions_ask_num')  

    # Получаем вопрос
    question: Question = test_manager.get_question(
        course_slug, 
        stage_num - 1, 
        question_num - 1, 
        questions_ask_index=questions_ask_num - 1
    ) 

    stage_questions_data, questions_count, question_type = test_manager.get_stage_questions_data(course_slug, stage_num - 1, question_num) 
    is_correct, comment = question.get_is_correct_status(answer=answer)

    # Если ответ не правильный то скидываем на начало курса
    if not is_correct:
        profile.drop_question_history(
            course_slug, 
            stage_num - 1
        )
        await state.update_data(
            user_data=profile.model_dump(),
            # stage_num=1,
            question_num=1,
        )

        text = '❌ Вы ответили неправильно. Попробуйте еще раз'
        if comment:
            text += f'\n\nℹ️{comment}'

        message_data = {
            'text': text,
            'chat_id': from_user_id,
            'parse_mode': 'html',
            'reply_markup': main_keyboards.get_menu_keyboard(
                course_slug=course_slug,
                stage_slug=main_utils.get_stage_slug(course_slug, 1),
                is_trained=profile.is_trained,
            ),
        }  
        message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)
        if is_sent:
            await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id])    
        return


    question_history = QuestionHistory(
        num=questions_ask_num, 
        type='open_questions',
        is_correct=is_correct,
        question=question.text,
        answer=answer,
    )

    profile.update_question_history(
        course_slug, 
        stage_num, 
        question_num,
        question_history,
    )

    await state.update_data(user_data=profile.model_dump())

    if question_num < questions_count:
        state_data = await state.update_data(
            question_num=question_num + 1
        )
        await testing(message, state)
    else:
        course_data = test_manager.get_course_data(course_slug)
        if stage_num < len(course_data):
            await state.update_data(
                stage_num=stage_num + 1,
                question_num=1,
            )
            stage_data = test_manager.get_stage_data(course_slug, stage_num)
            text = f"Тема завершена"  
            reply_markup = main_keyboards.get_menu_keyboard(course_slug , stage_data.get('slug'), profile.is_trained)

        else:
            completed_course_slugs_list: list = profile.completed_courses_slugs_list
            completed_course_slugs_list.append(course_slug)
            profile.completed_courses_slugs_list = completed_course_slugs_list

            if len(completed_course_slugs_list) < 1:
                await state.update_data(
                    stage_num=1,
                    question_num=1,
                )
                stage_data = test_manager.get_stage_data(course_slug, stage_num - 1)
                reply_markup = main_keyboards.get_menu_keyboard(course_slug , stage_data.get('slug'), False)
                text = f"Курс завершен"
            else:
                profile.is_trained = True
                await state.set_state(MainStatesGroup.neuro_consult)

                text = f"""
                    Обучение завершено 🎉🎉🎉
                    \nВы можете задать вопрос нейроконсультанту 🧑‍🔬
                """

            profile.save()


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


@main_router.message(
    MainStatesGroup.neuro_consult
)
async def neuro_consult(message: types.Message, state: FSMContext):
    '''
        Обработка сообщений в режиме нейро-консультанта
    '''
    from_user_id = message.chat.id
    await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 

    # Вопрос пользователя
    user_question = message.text

    # Ответ консультанта
    neuro_consultant_answer = await interface.get_neuro_consultant_answer(user_question)

    

    message_data = {
        'text': neuro_consultant_answer,    
        'chat_id': from_user_id,
        'parse_mode': 'html',
        'reply_markup': None,
    }  
    message, is_sent = await main_utils.edit_message_or_send(bot, state, message_data)

    if is_sent:
        await main_utils.append_value_state_data(state, 'previous_messages', [message.message_id]) 