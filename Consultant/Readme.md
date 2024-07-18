

```
Consultant/
├── consultant.py 
├── docx2md.py
├── knowledge_base.docx
├── knowledge_base.md
├── knowledge_base
│   ├── index.faiss
│   └── index.pkl
└── image
    └── media
        ├── image01.png
        ├── image02.png
        ├── ...
        └── image50.png
```
   
    **`consultant.py`** - основной файл консультанта
    **`docx2md.py`** - конвертер файлов docx в md формат
    **`knowledge_base.docx`** - загруженный с google docs файл базы знаний в docx формате
    **`knowledge_base.md`** - загруженный с google docs файл базы знаний в md формате
    **`knowledge_base`** - векторная база знаний в формате FAISS 
    **`image`** - папка с картинками к файлу базы знаний в формате md `knowledge_base.md`
    
    пример использования: 

    # путь к файлу базы знаний на google docs в формате docx
    docx_url = 'https://docs.google.com/document/d/16a_btcWVlSY0-c8Q5CwRg4UROm2-kG3Y/edit?usp=sharing&ouid=104476155406090369831&rtpof=true&sd=true'
    # путь куда сохраним векторную базу faiss
    faiss_db_name = 'Consultant/knowledge_base'

    ```
    from consultant import Basecreator Consultant
    ```

    # загрузка базы знаний из google docx,  конвертация в md и faiss, сохранение на диске запускаем только при инициации бота
    base = Basecreator(docx_url=docx_url, faiss_db_name=faiss_db_name)
    
    # модуль консультанта
    consultant = Consultant(faiss_db_name=faiss_db_name)
    
    # функция получения ответа от консультанта
    answer = asyncio.run(consultant.get_answer("Какие услуги предоставляет Элеком?"))
    
