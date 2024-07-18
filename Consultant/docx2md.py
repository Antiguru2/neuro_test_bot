import subprocess
import tkinter as tk
from tkinter import filedialog
import re

class Converter:
    def __init__(self, docsx_file, md_file):
        self.input_file = docsx_file
        self.output_file = md_file

    def choose_file(self):
        """Выбор файла"""
        root = tk.Tk()
        root.withdraw()

        self.input_file = filedialog.askopenfilename(
            title="Выберите файл DOCX для конвертации в маркдаун",
            filetypes=[("Все файлы", "*.*")]
        )

        if not self.input_file:
            raise ValueError("Файл не выбран")

    def convert_docx_to_md(self):
        """Конвертация .docx файла в .md файл с помощью pandoc и извлечение изображений в отдельную папку"""
        # self.output_file = "Consultant/document.md"  # без consultant сохраняет в основной каталог git
        # pandoc_command = f"pandoc --extract-media Consultant/image/ {self.input_file} -o {self.output_file}"
        pandoc_command = f"pandoc -f docx -t markdown_strict --wrap=none --extract-media Consultant/image/ {self.input_file} -o {self.output_file}"
        # pandoc_command = f"pandoc -f docx -t markdown --wrap=none --extract-media Consultant/image/ {self.input_file} -o {self.output_file}"

        
        subprocess.run(pandoc_command, shell=True)

    def clean_md_document(self):
        """Очистка от лишних символов в ссылке на картинку и сохранение обратно в тот же файл"""

        # Функция для дублирования строк, начинающихся на #, ## или ###
        def duplicate_headers(md_document):
            def repl(match):
                header = match.group(0).lstrip('#').strip()
                return f"{match.group(0)}\n{header}"
            
            # Регулярное выражение для поиска строк, начинающихся на #, ## или ###
            pattern = re.compile(r'^(#{1,3} .+)$', re.MULTILINE)
            
            # Замена найденных строк на дублированные
            return re.sub(pattern, repl, md_document)


        with open(self.output_file, 'r', encoding='utf-8') as f:
            md_document = f.read()
            print(f'Файл прочитан: {self.output_file}')

        md_document = re.sub(r'\{[^}]*}', '', md_document)
        # Удаление символа '>' в начале строк
        md_document = re.sub(r'^> ?', '', md_document, flags=re.MULTILINE)

        # Удаление обратных слешей
        md_document = md_document.replace('\\', '')

        # Используем регулярное выражение для преобразования строки
        md_document =  re.sub(r'<img src="([^"]+)"[^>]*>', r'![](\1)',  md_document)

        md_document = md_document.replace('![](Consultant/', '![](') # Consultant/ заменить на итоговый каталог где будет создаваться md
        md_document = md_document.replace('[[', '[')
        md_document = md_document.replace(']]', ']')

        # Дублирование строк маркдаун простым текстом
        md_document = duplicate_headers(md_document)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(md_document)
            print(f'Файл записан: {self.output_file}')


if __name__ == "__main__":
    docx_file = '.\Consultant\knowledge_base.docx'
    md_file = '.\Consultant\knowledge_base.md'

    converter = Converter(docx_file, md_file)
    # converter.choose_file()
    converter.convert_docx_to_md()
    converter.clean_md_document()