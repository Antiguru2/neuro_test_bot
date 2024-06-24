import random

from pprint import pprint
from interfaces import test_interface as interface
from models import (
    Question,
    StudyingHistory,
    CourseHistory,
    StageHistory,
    QuestionHistory,
)

class TestManager:

    def get_course_data(self, courses_slugs) -> list:
        courses_questions_data = []
        questions_data = interface.get_questions_data()
        if questions_data:
            courses_questions_data = questions_data.get(courses_slugs)    
        return courses_questions_data


    def get_stage_data(self, courses_slugs, stage_num) -> tuple:
        stage_data = {}
        courses_questions_data = self.get_course_data(courses_slugs)
        if courses_questions_data:
            stage_data: dict = courses_questions_data[stage_num]

        return stage_data
    

    def get_stage_questions_data(self, courses_slugs, stage_index, question_index) -> tuple:
        stage_questions_data = []
        questions_count = 0

        stage_data = self.get_stage_data(courses_slugs, stage_index)
        if stage_data:
            test_question_amount: int = stage_data.get('test_question_amount', 0)
            open_question_amount: int = stage_data.get('open_question_amount', 0)
            total_questions_count: int = test_question_amount + open_question_amount
            if question_index < test_question_amount:
                question_type = 'test_questions'
                questions_count = question_index
                stage_questions_data = stage_data.get(question_type)

            elif question_index <= total_questions_count:
                question_type = 'open_questions'
                questions_count = total_questions_count
                stage_questions_data = stage_data.get(question_type)

        return stage_questions_data, questions_count, question_type


    def get_question_data(self, courses_slugs, stage_index, question_index, questions_asked = {}, questions_ask_index = None) -> dict:
        # print('++++++++++++++get_question_data')
        question_data = {}
        stage_questions_data, questions_count, question_type = self.get_stage_questions_data(courses_slugs, stage_index, question_index)

        if stage_questions_data:
            if questions_ask_index:
                question_index = questions_ask_index
            else:
                questions_asked_list = questions_asked.get(question_type, [])
                questions_nums_list = [i + 1 for i in range(len(stage_questions_data))]
                next_questions_nums = [x for x in questions_nums_list if x not in questions_asked_list]

                if next_questions_nums:
                    # print('ЁЁЁ   next_questions_nums', next_questions_nums)
                    random_questions_num = random.choice(next_questions_nums)
                    question_index = random_questions_num - 1
                else:
                    if question_index >= len(stage_questions_data):
                        question_index = questions_count - question_index - 1
                    else:
                        question_index = question_index

            # print('question_index', question_index)
            question_data = stage_questions_data[question_index]
            question_data['num'] = question_index + 1
        return question_data
    
    def get_question(self, *args, **kwargs) -> dict:
        question_data = self.get_question_data(*args, **kwargs)
        return Question.model_validate(question_data)

    def get_total_balls(self, studying_history):
        points_count = 0
        for course_list in studying_history.values():
            for stage_history in course_list:
                for answer in stage_history:
                    if answer.get('is_correct'):
                        points_count += 1
        return points_count
    
