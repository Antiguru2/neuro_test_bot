import os
import json

from dotenv import load_dotenv
from datetime import datetime
from typing import (
    Optional,
    Any,
)
from pydantic import BaseModel

from interfaces import test_interface as interface

load_dotenv()

general_rate_slug = os.getenv('GENERAL_RATE_SLUG')

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
    completed_courses_slugs_list: list[str] = []
    studying_history: dict = {}

    @classmethod
    def get(
        cls, 
        telegram_id: int, 
        user_data: dict = {}
    ) -> 'Profile':
        '''
        Возвращает профиль по id или собирает из словаря user_data
        '''

        if not user_data:
            if not os.path.exists('profiles'):
                os.mkdir('profiles')
            file_path = cls.get_file_path(telegram_id)
            if os.path.exists(file_path):
                with open(file_path, mode='r') as f:
                    user_data = json.loads(f.read())
            else:
                start_of_use = int(datetime.now().timestamp())
                user_data = {
                    'telegram_id': telegram_id,
                    'start_of_use': start_of_use
                }  # Включаем telegram_id в данные
                with open(file_path, mode='w') as f:
                    f.write(json.dumps(user_data))    

        return cls.model_validate(user_data)
    
    @classmethod
    def get_file_path(cls, telegram_id: int) -> str:
        return f'profiles/{telegram_id}.json'
    
    def save(self):
        with open(self.file_path, mode='w') as f:
            f.write(json.dumps(self.model_dump()))

    def update_question_history(
        self,
        course_slug: str, 
        stage_num: int, 
        question_num: int,
        history_object: Any,
    ) -> None:
        if course_slug and stage_num and question_num and history_object:
            course_history: list = self.studying_history.get(course_slug, [])
            if stage_num <= len(course_history):
                stage_history = course_history.pop(stage_num - 1)
            else:
                stage_history = []


            if question_num <= len(stage_history):    
                stage_history.pop(question_num - 1)

            stage_history.insert(question_num - 1, history_object.model_dump())
            course_history.insert(stage_num - 1, stage_history)
            self.studying_history[course_slug] = course_history

        self.save()

    def drop_question_history(
        self,
        course_slug: str, 
    ) -> None:
        self.studying_history[course_slug] = []
        self.save()
        

    @property
    def file_path(self) -> str:
        return f'profiles/{self.telegram_id}.json'
    
    def get_next_course_slug(self) -> str:
        completed_courses_count = len(self.completed_courses_slugs_list)
        if completed_courses_count == 0:
            course_slug = general_rate_slug
        elif completed_courses_count == 1:
            course_slug = self.departament
        else:
            raise ValueError('Добавьте обработку третьего курса')
        return course_slug
    
    def get_questions_asked(
        self, 
        course_slug: str, 
        stage_num: int,
    ) -> dict:
        questions_asked = {}
        course_history = self.studying_history.get(course_slug, [])

        if course_history:
            stage_history = course_history[stage_num - 1]

            for question in stage_history:
                question_type = question.get('type')
                question_num = question.get('num')
                questions_asked_list = questions_asked.get(question_type, [])
                questions_asked_list.append(question_num)
                questions_asked[question_type] = questions_asked_list

        return questions_asked


class StudyingHistory(BaseModel):
    '''
    '''
    courses: dict = {}

    def get_scourses(self) -> 'CourseHistory':
        scourses = []
        for course_slug, stages in self.courses.items():
            scourses.append(CourseHistory(
                slug=course_slug,
                stages=stages,
            ))
        return scourses

    def get_course_history(self, slug) -> 'CourseHistory':
        scourse = CourseHistory(
            slug=slug,
            stages=self.courses.get(slug, []),
        )
        return scourse


class CourseHistory(BaseModel):
    '''
    '''
    slug: str 
    stages: list = []

    def get_stage_history(self, num) -> 'StageHistory':
        stage_history_data = []
        if self.stages:
            try:
                stage_history_data: list = self.stages[num - 1]
            except IndexError:
                pass

        return StageHistory(
            num=num,
            questions=stage_history_data
        )

class StageHistory(BaseModel):
    '''
    '''
    num: int 
    questions: list = []

    def get_question_history(self, num) -> 'QuestionHistory':
        questions_history_data = []
        if self.questions:
            try:
                questions_history_data: list = self.questions[num - 1]
            except IndexError:
                pass

        return QuestionHistory(**questions_history_data)


class QuestionHistory(BaseModel):
    '''
    '''
    num: int 
    type: str
    is_correct: bool = False
    question: Optional[str] = None
    answer: Optional[str] = None



class Question(BaseModel):
    num: int 
    text: str
    answers: list = []
    correct_answer: Optional[str] = None
    context: Optional[str] = None

    def get_is_correct_status(
        self, 
        answer_index: Optional[int] = None,
        answer: Optional[str] = None,
    ) -> bool:
        is_correct = False
        if answer_index != None and self.correct_answer and self.answers:
            answer = self.answers[answer_index]
            if self.correct_answer == answer:
                is_correct = True

        elif self.context and answer:
            is_correct = interface.verification_correct_answer(self, answer)

        else:
            raise ValueError(f"""
                Такой вопрос не поддерживается
                Данные:
                    answer_index: {answer_index}
                    answer: {answer}
                    self.correct_answer: {self.correct_answer}
                    self.context: {self.context}
                    self.answers: {self.answers}
            """)
        
        return is_correct