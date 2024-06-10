import os
import json

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Profile(BaseModel):
    '''
    Модель профиля
    '''
    telegram_id: int
    start_of_use: Optional[int] = None
    username: Optional[str] = None
    departament: Optional[str] = None
    is_registered: bool = False
    is_trained: bool = False
    completed_course_slugs_list: list[str] = []
    studying_history: list[list[dict]] = []
    @classmethod
    def get(cls, telegram_id: int) -> 'Profile':
        '''
        Возвращает профиль по id
        '''
        if not os.path.exists('profiles'):
            os.mkdir('profiles')
        file_path = cls.get_file_path(telegram_id)
        if os.path.exists(file_path):
            with open(file_path, mode='r') as f:
                user_data = json.loads(f.read())
        else:
            start_of_use = int(datetime.now().timestamp())
            user_data = {
                'start_of_use': start_of_use
            }  # Включаем telegram_id в данные
            with open(file_path, mode='w') as f:
                f.write(json.dumps(user_data))    
        user_data['telegram_id'] = telegram_id  
        print('user_data', user_data)
        return cls.model_validate(user_data)
    @classmethod
    def get_file_path(cls, telegram_id: int) -> str:
        return f'profiles/{telegram_id}.json'
    def save(self):
        with open(self.file_path, mode='w') as f:
            f.write(json.dumps(self.model_dump()))
    @property
    def file_path(self) -> str:
        return f'profiles/{self.telegram_id}.json'