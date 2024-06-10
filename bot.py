# -*- coding: utf-8 -*-
import os
import json
import asyncio
import logging
import requests
import aiofiles

from email import message
from ntpath import join
from threading import active_count
from dotenv import load_dotenv
from datetime import datetime, timedelta


from aiogram import (
    Bot, 
    Dispatcher, 
    Router, 
    F, 
    types, 
    utils,
)

# from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.scene import Scene, SceneRegistry
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import default_state
from aiogram.fsm import state

load_dotenv()

token = os.getenv('BOT_TOKEN')
general_rate_slug = os.getenv('GENERAL_RATE_SLUG')

bot = Bot(token=token)

class MainStatesGroup(state.StatesGroup):
    '''
        Основные состояния
    '''
    registration = state.State()
    studying = state.State()
    testing = state.State()
    neuro_consult = state.State()


from main import handlers as main_handlers
from main import utils as main_utils


# Запуск бота
def create_dispatcher():
    # Event isolation is needed to correctly handle fast user responses
    dispatcher = Dispatcher(
        events_isolation=SimpleEventIsolation(),
    )
    dispatcher.include_router(main_handlers.main_router)

    return dispatcher


async def main():
    '''
        Функция зарускающая бота
    '''
    dispatcher = create_dispatcher()

    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг

    await bot.delete_webhook(drop_pending_updates=True) # TODO Убрать на проде
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Процесс остановлен.")     
    except Exception as error:
        main_utils.send_message_about_error(
            'Бот сломался!!!',
            'Нейро-тест бот',
            error,
        )

    logging.basicConfig(level=logging.INFO)