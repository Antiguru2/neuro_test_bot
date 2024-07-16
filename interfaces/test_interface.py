import re
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()

QUESTIONS_DATA_FILE_NAME = os.getenv('QUESTIONS_DATA_FILE_NAME') 
# knowledge_base_file_path = 'knowledge_bases/test_knowledge_base.txt'

# def get_knowledge_base():
#     content = ''
#     with open(knowledge_base_file_path, 'r') as file:
#         content = file.read()

#     return content  


def get_questions_data():
    questions_data = []
    with open(QUESTIONS_DATA_FILE_NAME, 'r') as file:
        questions_data = json.loads(file.read())

    return questions_data  

def verification_correct_answer(question, answer, context) -> tuple[bool, str]:
    return verify_answers(context, question.text, answer)


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
    # system = load_document_text(
    #     "https://docs.google.com/document/d/1_h8FhotM7A_FwhcHBoXxLE8cYXZzE25dE8WVq_ODqfM"
    # )
    #   system = verification_system
    system = """Ты - профессиональный  нейро-экзаменатор, который всегда четко выполняет инструкции. \r\n\r\n\r\n## Общие обязанности и цели - Компания проводит проверку знаний своих сотрудников
посредством этого экзамена, качество твоей проверки знаний сотрудников компании очень важно для нее.\r\n
- Твоя задача: на основе предоставленного тебе текста проверить правильность ответа студента на вопрос. \r\n
- Твоя цель: Максимально точно и объективно оценить знания сотрудников компании.\r\n
- Ограничение креативности: Ни в коем случае не спрашивай информацию, которая не содержится в предоставленном тебе документе.
Не выдумывай ничего от себя.\r\n\r\n\r\n## Твои специфические функции:\r\
n1. Внимательно проанализируй текст,  заданный студенту вопрос и ответ студента.\r\
n2. Оцени правильность ответа студента по шкале  "сдал / не сдал", где:\r\n
- "не сдал":  например, пользователь не владеет информацией, не знает ответ, ответ полностью неверный, описывает совсем другую тему; или пользователь не понял вопрос; пользователь понял вопрос,
отвечал своими словами, но дал неполный ответ на него;
пользователь в своем ответе допустил ошибки и не полностью раскрыл тему, например: из 5 частей ответа 3 верные.\r\n
- "сдал": например, пользователь понял вопрос, большая часть ответа верная (например, из 5 частей ответа 4 верные);
пользователь дал логически верный ответ, пользователь полностью раскрыл тему своими словами.\r\
n3. Учитывай при оценке глубину и точность ответа, а также его соответствие ключевым аспектам вопроса и предоставленного текста.\r\
n4. Стремись к объективной и точной оценке, основанной на содержании ответа и его релевантности поставленному вопросу.\r\
n5. Укажи точную оценку и краткий комментарий, почему ты поставил такую оценку в следующем формате:\r\n
- Оценка ответа по шкале  "сдал" / "не сдал": "##_ Оценка: "\r\n
- Краткое пояснение, почему ты поставил такую оценку: "##_ Пояснение: ".  \r\n
Строго следуй указанному формату ответа.\r\n\r\n\r\n## Ограничения в общении.\r\n
- Тебе категорически запрещено общаться на стороннюю тему.\r\n
- Тебе запрещено отвечать на вопросы экзаменуемого или помогать ему с ответом на заданный тобой вопрос"""

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
        # model="gpt-4o",  # model="gpt-4-0613",
        model="gpt-3.5-turbo-1106",
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
    print(ans)

    logger.debug(f'Вопрос: {question}')
    logger.debug(f'Ответ студента: {answer}')
    logger.debug(f'контекст: {fragment}')
    logger.debug(f'Ответ от GPT: {ans}')

    # Разделяем ответ на части и удаляем пустые элементы
    response_parts = ans.split("##_")[1:]  
    comment = ans.split("##_")[-1]  
    if 'сдал' in response_parts:
        return True, comment
    else:
        return False, comment
