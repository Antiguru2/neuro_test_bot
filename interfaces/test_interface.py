import re
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

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
    return verify_answers(context, question, answer)


async def get_neuro_consultant_answer(user_question: str) -> str:
    neuro_consultant_answer = 'Ответ не известен.'
    
    # Здесь должен быть код, который возвращает ответ консультанта

    return neuro_consultant_answer


def load_document_text(url: str) -> str:
    # Extract the document ID from the URL
    match_ = re.search("/document/d/([a-zA-Z0-9-_]+)", url)
    if match_ is None:
        raise ValueError("Invalid Google Docs URL")
    doc_id = match_.group(1)
    response = requests.get(
        f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    )
    response.raise_for_status()
    text = response.text
    return text




client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)

# verification_system = load_document_text('https://docs.google.com/document/d/1_h8FhotM7A_FwhcHBoXxLE8cYXZzE25dE8WVq_ODqfM')


def verify_answers(fragment, question, answer):
    system = load_document_text(
        "https://docs.google.com/document/d/1_h8FhotM7A_FwhcHBoXxLE8cYXZzE25dE8WVq_ODqfM"
    )
    #   system = verification_system

    user_assist = """Оцени правильность ответа студента на вопрос по тексту по шкале  "сдал" / "не сдал". Текст: 'Теоретический аспект: при исследовании
        некоторой задачи результаты теории алгоритмов позволяют ответить на вопрос – является ли эта задача в принципе алгоритмически разрешимой
        – для алгоритмически неразрешимых задач возможно их сведение к задаче останова машины Тьюринга. В случае алгоритмической разрешимости задачи
        – следующий важный теоретический вопрос – это вопрос о принадлежности этой задачи к классу NP–полных задач, при утвердительном ответе на который,
        можно говорить о существенных временных затратах для получения точного решения для больших размерностей исходных данных.' Вопрос: 'Какой вопрос
        задают теоретики алгоритмов при исследовании алгоритмической разрешимости задачи после установления её разрешимости?'. Ответ студента: 'После
        определения того, что задача алгоритмически разрешима, специалисты в области теории алгоритмов ставят вопрос о том, относится ли эта задача
        к классу NP-полных задач. Если ответ на этот вопрос положительный, это указывает на то, что для нахождения точного решения задачи, особенно
        когда речь идет о большом объеме исходных данных, потребуются значительные временные ресурсы.' """

    assist = """##_сдал##_ Пояснение: ответ студента полностью соответствует заданному вопросу, он точно отражает ключевые аспекты текста и хорошо структурирован"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",  # model="gpt-4-0613",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_assist},
            {"role": "assistant", "content": assist},
            {
                "role": "user",
                "content": f"Оцени правильность ответа студента на вопрос по тексту по шкале  сдал / не сдал. Текст:  '{fragment}'. Вопрос: '{question}', Ответ студента: '{answer}'",
            },
        ],
    )
    ans = response.choices[0].message.content
    # Разделяем ответ на части и удаляем пустые элементы
    print("ans", ans)
    response_parts = ans.split("##_ ")[
        1:
    ]  
    if 'сдал' in response_parts:
        return True
    else:
        return False
