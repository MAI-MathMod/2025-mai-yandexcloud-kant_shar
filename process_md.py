import re
import pandas as pd
from typing import List, Tuple

def parse_md_file(file_path: str) -> List[Tuple[str, str]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Регулярное выражение для поиска записей
    pattern = r'\*\*ID \d+\*\* \(.*?\)<br>(.*?)(?=\*\*ID \d+\*\*|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # Очистка текста от лишних пробелов и переносов строк
    matches = [text.strip() for text in matches]
    
    # Создание пар вопрос-ответ
    qa_pairs = []
    for i in range(0, len(matches)-1, 2):
        if i+1 < len(matches):
            qa_pairs.append((matches[i], matches[i+1]))
    
    return qa_pairs

def save_to_csv(qa_pairs: List[Tuple[str, str]], output_file: str):
    df = pd.DataFrame(qa_pairs, columns=['question', 'answer'])
    df.to_csv(output_file, index=False, encoding='utf-8')

if __name__ == "__main__":
    # Пример использования
    qa_pairs = parse_md_file('2021.md')
    save_to_csv(qa_pairs, '2021_qa.csv') 