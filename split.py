import json
import math
import os

def split_json_file(input_path, num_files, year):
    try:
        # Чтение исходного JSON
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверка наличия ключа 'messages'
        if 'messages' not in data:
            raise KeyError("Ключ 'messages' не найден в JSON-файле")
        
        messages = data['messages']
        total_messages = len(messages)
        
        # Проверка корректности num_files
        if num_files <= 0:
            raise ValueError("Количество выходных файлов должно быть больше 0")
        if num_files > total_messages:
            raise ValueError(f"Количество файлов ({num_files}) превышает количество сообщений ({total_messages})")
        
        # Вычисление размера каждой части
        chunk_size = math.ceil(total_messages / num_files)
        
        # Разделение сообщений на части
        for i in range(num_files):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, total_messages)
            
            # Создание нового JSON с той же структурой
            new_data = data.copy()
            new_data['messages'] = messages[start_idx:end_idx]
            
            # Сохранение в новый файл
            output_path = f'{year}_{i+1}.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            print(f"Сохранён файл {output_path} с {len(new_data['messages'])} сообщениями")
    
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_path} не найден")
    except json.JSONDecodeError:
        print("Ошибка: Некорректный формат JSON")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

# Пример использования
if __name__ == "__main__":
    
    year = 2024
    num_output_files = 35

    split_json_file(f"{year}/{year}.json", num_output_files, year)