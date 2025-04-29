import re

def remove_duplicate_messages(input_file, output_file, year):
    # Список для хранения уникальных строк с ID
    unique_messages = {}
    # Словарь для подсчёта вхождений каждого ID
    id_counts = {}
    # Флаг для отслеживания, находится ли код внутри таблицы
    in_table = False
    # Список для хранения всех строк файла
    output_lines = []

    # Регулярное выражение для поиска строк с ID
    id_pattern = re.compile(r'\|\s*\*\*ID\s*(\d+)\*\*')

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        # Проверяем, является ли строка началом таблицы
        if line.strip().startswith('| Вопросы | Ответы |'):
            in_table = True
            output_lines.append(line)
            continue
        # Проверяем, является ли строка разделителем таблицы
        elif in_table and line.strip().startswith('|-'):
            output_lines.append(line)
            continue
        # Если строка пустая или не относится к таблице, сохраняем её как есть
        elif not line.strip().startswith('|') or not in_table:
            in_table = False
            output_lines.append(line)
            continue

        # Если строка содержит ID, проверяем на дубликат
        match = id_pattern.search(line)
        if match:
            message_id = match.group(1)
            # Увеличиваем счётчик вхождений ID
            id_counts[message_id] = id_counts.get(message_id, 0) + 1
            # Сохраняем только первое вхождение сообщения с данным ID
            if message_id not in unique_messages:
                unique_messages[message_id] = line
                output_lines.append(line)
        else:
            # Если строка таблицы не содержит ID (например, продолжение ответа), добавляем её
            output_lines.append(line)

    # Записываем результат в новый файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    # Формируем словарь с ID, которые повторялись более 1 раза
    duplicates = {id: count for id, count in id_counts.items() if count > 1}
    
    input_file = f'{year}/{year}.md'
    output_file = f'{year}_cleaned.md'

    print(f"Дубликаты удалены. Результат сохранён в {output_file}")

    if duplicates:
        for item in duplicates.items():
            print(f"ID: {item[0]}: {item[1]}")
    else:
        print("Повторяющихся ID не найдено")


year = 2023

remove_duplicate_messages(f"{year}/{year}.md", f"{year}_cleaned.md", year)
