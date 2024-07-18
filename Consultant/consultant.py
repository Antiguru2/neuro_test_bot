import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
import importlib
from Consultant.docx2md import Converter
import requests
import re
from dotenv import load_dotenv
import os
import asyncio

from openai import AsyncOpenAI

# получим переменные окружения из .env
load_dotenv()

# API-key
openai.api_key = os.environ.get("OPENAI_API_KEY")


class Basecreator:
    def __init__(self, docx_url, faiss_db_name):
        self.docx_url = docx_url # путь к файлу базы знаний на google docs в формате docx
        self.faiss_db_name = faiss_db_name  # путь куда сохраним векторную базу faiss

        self.docx_file = f'{faiss_db_name}.docx'  # путь куда сохраним файл базы знаний в docx
        print(' self.docx_file: ',self.docx_file)
        self.md_file = f'{faiss_db_name}.md' # путь куда сохраним файл базы знаний в md
        print('self.md_file: ', self.md_file)


        self.google_docx_to_md()
        self.create_index_base()

    def load_document_text(self) -> str:
        ''' функция для загрузки документа docx по ссылке из гугл драйв '''

        # Extract the document ID from the URL
        match_ = re.search('/document/d/([a-zA-Z0-9-_]+)', self.docx_url)
        if match_ is None:
            raise ValueError('Invalid Google Docs URL')
        doc_id = match_.group(1)

        # Download the document as plain text
        response = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=docx')
        response.raise_for_status()
        text = response.content

        with open(self.docx_file, 'wb') as f:
            f.write(response.content)

        return text

    def google_docx_to_md(self):
        ''' функция загрузки базы из google docx, конвертация в md и сохранения на диске '''

        self.load_document_text()

        # конвертация в md для базы знаний
        converter = Converter(self.docx_file, self.md_file)
        # converter.choose_file()
        converter.convert_docx_to_md()
        converter.clean_md_document()
        # mdTOdocx.convert_docx_to_md(docx_file, self.path_to_base)
        return    

    def read_document(self):
        ''' чтение md файла'''

        with open(self.md_file, 'r', encoding='utf-8') as file:
            return file.read()

    def create_index_base(self):
        ''' создание базы faiss'''

        document = self.read_document()
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        source_chunks = splitter.split_text(document)
        print(f'\n\nТекст разбит на {len(source_chunks)} чанков.')
        embeddings = OpenAIEmbeddings()
        # self.faiss_db = FAISS.from_documents(source_chunks, embeddings)
        self.faiss_db = FAISS.load_local(self.faiss_db_name, embeddings, allow_dangerous_deserialization=True)


        self.faiss_db.save_local(self.faiss_db_name)
        
        return self.faiss_db
    
    # def save_faiss_db(self):
    #     self.faiss_db.save_local(self.faiss_db_name)
    #     return


class Consultant:
    def __init__(self, faiss_db_name):
        self.faiss_db_name = faiss_db_name
        self.faiss_db = self.load_faiss_db()
        self.client = AsyncOpenAI()

    def load_faiss_db(self):
        embeddings = OpenAIEmbeddings()
        # self.faiss_db = FAISS.load_local(self.faiss_db_name, embeddings)
        self.faiss_db = FAISS.load_local(self.faiss_db_name, embeddings, allow_dangerous_deserialization=True)

        return self.faiss_db

    async def get_answer(self, query):
        docs = self.faiss_db.similarity_search(query, k=2)
        message_content = '\n\n'.join([f'{doc.page_content}' for doc in docs])
        # print("Найдены чанки:")
        # print(f'\n{message_content}\n')
        # print("="*150)
        # print()

        system = """ Вы консультант службы поддержки работников в компании Элеком. 
        Ваша задача — предоставить точную и обстоятельную информацию о требованиях и процедурах, предусмотренных регламентами компании. 
        Перед началом работы вам будет представлена информация, включающая выдержки из регламентов и текущий вопрос работника. 
        Ваша обязанность — ответить на вопросы работника, полагаясь исключительно на предоставленные документы. 
        Особенно тщательно обращайте внимание на точность данных о правильности проведения регламентированных процедур. 
        В своих ответах обязательно давайте ссылки на картинки, регламенты и инструкции из предоставлекак создать договор?нных вам документов, если это входит в контекст ответа. 
        
        Пример правильного ответа:
        1. **Переход на вкладку "Договоры" и создание договора:**
         ![](image/media/image6.png)
        - Перейдите на вкладку "Договоры" в программе 1С.
        - Нажмите кнопку "Создать".
        ![](image/media/image9.png)
        - Введите цель договора и его наименование.
        - Укажите организацию, с которой будет вестись взаимодействие.
        - Заполните необходимые данные и перейдите на вкладку "Расчеты и оформление".
        ![](image/media/image10.png)

        Пример неправильного ответа:
        1. **Переход на вкладку "Договоры" и создание договора:**
        - Перейдите на вкладку "Договоры" в программе 1С.
        - Нажмите кнопку "Создать".
        - Введите цель договора и его наименование.
        - Укажите организацию, с которой будет вестись взаимодействие.
        - Заполните необходимые данные и перейдите на вкладку "Расчеты и оформление".
        
        Не добавляйте информацию из внешних источников! Если работник задал вопрос не касающийся регламентов и процедур в компании Элеком, сообщите, что вы не можете общаться на другие темы.
        Начинайте общение сразу с ответа, избегая приветствий."""

        user = f"""Работник задал вопрос. Используйте предоставленные вам отрывки из регламентов и процедур компании, 
        чтобы ответить на вопрос работника. Не придумывайте ничего от себя. 
        Ответ должен быть основан только на информации из предоставленных документов.
        Если в предоставленной вам информации нет ответа на вопрос работника, скажите: "У меня нет такой информации".
        Ваш ответ должен очень подробно передавать текст документа вместе с ссылками на картинки и документы.
        Документы с информацией для ответа работнику: {message_content}\n\nВопрос работника: \n{query}"""

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        # completion = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo-0125",
        #     messages=messages,
        #     temperature=0
        # )

        # получение ответа от chatgpt
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            temperature=0
        )

        return completion.choices[0].message.content 

# Пример использования
if __name__ == '__main__':

    # путь к файлу базы знаний на google docs в формате docx
    docx_url = 'https://docs.google.com/document/d/16a_btcWVlSY0-c8Q5CwRg4UROm2-kG3Y/edit?usp=sharing&ouid=104476155406090369831&rtpof=true&sd=true'
    # путь куда сохраним векторную базу faiss
    faiss_db_name = 'Consultant/knowledge_base'

    # загрузка базы знаний из google docx,  конвертация в md и faiss, сохранение на диске запускаем только при инициации бота
    base = Basecreator(docx_url=docx_url, faiss_db_name=faiss_db_name)
    # ####################################################################
    
    # модуль консультанта
    consultant = Consultant(faiss_db_name=faiss_db_name)
    
    # функция получения ответа от консультанта
    answer = asyncio.run(consultant.get_answer("Как завести новый договор?"))
    # answer = consultant.get_answer("Какие услуги предоставляет Элеком?")
    print(answer)

