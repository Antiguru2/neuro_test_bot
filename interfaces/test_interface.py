import re
import json

knowledge_base_file_path = 'knowledge_bases/test_knowledge_base.txt'

def get_knowledge_base():
    content = ''
    with open(knowledge_base_file_path, 'r') as file:
        content = file.read()

    return content  


questions_data_file_path = 'questions_data.json'

def get_questions_data():
    questions_data = []
    with open(questions_data_file_path, 'r') as file:
        questions_data = json.loads(file.read())

    return questions_data  

def verification_correct_answer(question, answer, context) -> bool:
    return True


async def get_neuro_consultant_answer(user_question: str) -> str:
    neuro_consultant_answer = 'Ответ не известен.'
    
    # Здесь должен быть код, который возвращает ответ консультанта

    return neuro_consultant_answer