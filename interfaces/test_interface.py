import re

file_path = 'knowledge_bases/test_knowledge_base.txt'

def get_knowledge_base():
    with open(file_path, 'r') as file:
        content = file.read()

    return content   