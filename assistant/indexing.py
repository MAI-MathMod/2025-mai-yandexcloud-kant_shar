"""
Модуль для анализа текстовых файлов
"""

from glob import glob
from pathlib import Path
from dotenv import load_dotenv
from yandex_cloud_ml_sdk.search_indexes import (
    StaticIndexChunkingStrategy,
    HybridSearchIndexType,
    ReciprocalRankFusionIndexCombinationStrategy,
)
import os
from yandex_cloud_ml_sdk import YCloudML
from config import Config

# Initialize SDK
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
config = Config(_env_file=env_path)
sdk = YCloudML(folder_id=config.folder_id, auth=config.api_key)

# Инициализация SDK для токенизации
model = sdk.models.completions("yandexgpt", model_version="rc")

# Оптимальный размер чанка (1000 токенов)
CHUNK_SIZE = 1000 * 2  # 1000 токенов * 2 символа/токен


def get_token_count(filename):
    """Подсчёт количества токенов в файле"""
    with open(filename, "r", encoding="utf8") as f:
        content = f.read()
        tokens = len(model.tokenize(content))
        chars = len(content)
        ratio = chars / tokens
        print(f"{os.path.basename(filename)}: {tokens} токенов, {ratio:.2f} chars/token")
        return tokens


def get_file_len(filename):
    """Подсчёт количества символов в файле"""
    with open(filename, encoding="utf-8") as f:
        l = len(f.read())
    return l


def chunk_and_upload_file(filename):
    """Разбиение файла на чанки и загрузка в облако"""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Определяем тип файла по пути
    if "facts" in filename:
        return chunk_and_upload_facts(content)
    elif "docs" in filename:
        return chunk_and_upload_docs(content)
    elif "institutes" in filename:
        return chunk_and_upload_institutes(content)
    else:
        return chunk_and_upload_chats(content)


def chunk_and_upload_facts(content):
    """Разбиение файла с фактами на чанки и загрузка в облако"""
    chunks = []

    # Разбиваем содержимое на строки
    lines = content.split("\n")

    # Определяем тип файла по первой строке
    if lines[0].startswith("# Факты о МАИ от студентов"):
        # Обработка Facts.md (табличный формат)
        # Пропускаем заголовок
        if lines[0].startswith("#"):
            lines = lines[1:]

        # Пропускаем заголовок таблицы и разделитель
        if lines[0].startswith("|"):
            lines = lines[2:]

        # Обрабатываем каждую строку таблицы
        for line in lines:
            if not line.strip() or not line.startswith("|"):
                continue

            # Разделяем строку на ячейки
            cells = [cell.strip() for cell in line.split("|")[1:-1]]

            # Создаем чанк для каждой непустой ячейки
            for i, cell in enumerate(cells):
                if not cell:
                    continue

                # Определяем категорию по позиции
                categories = ["Учебный процесс", "Инфраструктура", "Студенческая жизнь",
                            "История и уникальность", "Международные возможности"]
                category = categories[i] if i < len(categories) else "Другое"

                # Форматируем факт
                fact = f"""Категория: {category}
Факт: {cell}"""

                # Загружаем чанк
                chunk_id = sdk.files.upload_bytes(
                    fact.encode(),
                    ttl_days=1,
                    expiration_policy="static",
                    mime_type="text/markdown"
                )
                chunks.append(chunk_id)
    else:
        # Обработка more_facts.md (markdown формат)
        current_category = ""
        current_facts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Определяем уровень заголовка
            if line.startswith("### "):
                # Сохраняем предыдущую категорию
                if current_category and current_facts:
                    fact = f"""Категория: {current_category}
Факты:
{chr(10).join(current_facts)}"""

                    chunk_id = sdk.files.upload_bytes(
                        fact.encode(),
                        ttl_days=1,
                        expiration_policy="static",
                        mime_type="text/markdown"
                    )
                    chunks.append(chunk_id)

                current_category = line[4:]  # Убираем "### "
                current_facts = []

            elif line.startswith("* "):
                # Это факт
                fact_text = line[2:]  # Убираем "* "
                current_facts.append(fact_text)

            elif line.startswith("  * "):
                # Это подфакт
                fact_text = line[4:]  # Убираем "  * "
                if current_facts:
                    # Добавляем к последнему факту
                    current_facts[-1] += f"\n  - {fact_text}"
                else:
                    current_facts.append(f"- {fact_text}")

        # Сохраняем последнюю категорию
        if current_category and current_facts:
            fact = f"""Категория: {current_category}
Факты:
{chr(10).join(current_facts)}"""

            chunk_id = sdk.files.upload_bytes(
                fact.encode(),
                ttl_days=1,
                expiration_policy="static",
                mime_type="text/markdown"
            )
            chunks.append(chunk_id)

    return chunks


def chunk_and_upload_docs(content):
    """Разбиение файла с документами на чанки и загрузка в облако"""
    chunks = []

    # Пропускаем заголовок
    lines = content.split("\n")
    if lines[0].startswith("#"):
        lines = lines[1:]

    # Пропускаем заголовок таблицы и разделитель
    if lines[0].startswith("|"):
        lines = lines[2:]

    # Обрабатываем каждую строку таблицы
    for line in lines:
        if not line.strip() or not line.startswith("|"):
            continue

        # Разделяем строку на ячейки
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) >= 3:
            keywords = cells[0].strip()
            question = cells[1].strip()
            answer = cells[2].strip()

            # Форматируем документ
            doc = f"""Ключевые слова: {keywords}
Вопрос: {question}
Ответ: {answer}"""

            # Загружаем чанк
            chunk_id = sdk.files.upload_bytes(
                doc.encode(),
                ttl_days=1,
                expiration_policy="static",
                mime_type="text/markdown"
            )
            chunks.append(chunk_id)

    return chunks


def chunk_and_upload_institutes(content):
    """Разбиение файла с описаниями институтов и программ на чанки и загрузка в облако"""
    chunks = []
    current_institute = ""
    current_program = ""
    current_description = []

    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("# "):
            # Это название направления (из courses.md)
            if current_institute and current_program:
                # Сохраняем предыдущий чанк
                description = "\n".join(current_description) if current_description else "Описание отсутствует"
                fact = f"""Направление: {current_institute}
Программа: {current_program}
Описание: {description}"""

                chunk_id = sdk.files.upload_bytes(
                    fact.encode(),
                    ttl_days=1,
                    expiration_policy="static",
                    mime_type="text/markdown"
                )
                chunks.append(chunk_id)

            current_institute = line[2:]  # Убираем "# "
            current_program = ""
            current_description = []

        elif line.startswith("## "):
            # Это название программы (из courses.md)
            if current_institute and current_program:
                # Сохраняем предыдущий чанк
                description = "\n".join(current_description) if current_description else "Описание отсутствует"
                fact = f"""Направление: {current_institute}
Программа: {current_program}
Описание: {description}"""

                chunk_id = sdk.files.upload_bytes(
                    fact.encode(),
                    ttl_days=1,
                    expiration_policy="static",
                    mime_type="text/markdown"
                )
                chunks.append(chunk_id)

            current_program = line[3:]  # Убираем "## "
            current_description = []

        elif line.startswith("Институт №"):
            # Это название института (из institutes.md)
            if current_institute:
                # Сохраняем предыдущий чанк
                description = "\n".join(current_description) if current_description else "Описание отсутствует"
                fact = f"""Институт: {current_institute}
Описание: {description}"""

                chunk_id = sdk.files.upload_bytes(
                    fact.encode(),
                    ttl_days=1,
                    expiration_policy="static",
                    mime_type="text/markdown"
                )
                chunks.append(chunk_id)

            current_institute = line
            current_program = ""
            current_description = []

        else:
            # Это описание программы или института
            current_description.append(line)

    # Сохраняем последний чанк
    if current_institute:
        description = "\n".join(current_description) if current_description else "Описание отсутствует"
        if current_program:
            fact = f"""Направление: {current_institute}
Программа: {current_program}
Описание: {description}"""
        else:
            fact = f"""Институт: {current_institute}
Описание: {description}"""

        chunk_id = sdk.files.upload_bytes(
            fact.encode(),
            ttl_days=1,
            expiration_policy="static",
            mime_type="text/markdown"
        )
        chunks.append(chunk_id)

    print(f"Total chunks created: {len(chunks)}")
    return chunks


def chunk_and_upload_chats(content):
    """Разбиение файла с чатами на чанки и загрузка в облако"""
    # Пропускаем заголовок и начало таблицы
    lines = content.split("\n")
    if lines[0].startswith("#"):
        year = lines[0].strip("#").strip()
        lines = lines[1:]
    else:
        year = "unknown"

    if lines[0].startswith("| Вопросы | Ответы |"):
        lines = lines[2:]  # Пропускаем заголовок таблицы и разделитель

    # Разбиваем на диалоги
    chunks = []

    for line in lines:
        if not line.strip():  # Пропускаем пустые строки
            continue

        # Разделяем строку на вопрос и ответ
        parts = line.split("|")
        if len(parts) < 4:  # Пропускаем некорректные строки
            continue

        # Извлекаем ID и дату из вопроса
        question_parts = parts[1].strip().split("<br>")
        if len(question_parts) > 1:
            metadata = question_parts[0].strip()
            question = question_parts[1].strip()
        else:
            metadata = ""
            question = parts[1].strip()

        # Извлекаем ID и дату из ответа
        answer_parts = parts[2].strip().split("<br>")
        if len(answer_parts) > 1:
            answer_metadata = answer_parts[0].strip()
            answer = answer_parts[1].strip()
        else:
            answer_metadata = ""
            answer = parts[2].strip()

        # Форматируем диалог с метаданными
        dialog = f"""Год: {year}
Вопрос ({metadata}):
{question}

Ответ ({answer_metadata}):
{answer}"""

        # Загружаем каждый диалог как отдельный чанк
        chunk_id = sdk.files.upload_bytes(
            dialog.encode(),
            ttl_days=1,
            expiration_policy="static",
            mime_type="text/markdown"
        )
        chunks.append(chunk_id)

    return chunks


def create_and_populate_search_index(chunks, index_name, batch_size=100):
    """Создание поискового индекса и добавление чанков пакетами"""
    if not chunks:
        raise ValueError("No chunks provided for indexing")

    print(f"\nСоздание поискового индекса...")

    # Создаем индекс с первым пакетом чанков (до batch_size)
    initial_batch = chunks[:batch_size]
    op = sdk.search_indexes.create_deferred(
        initial_batch,
        index_type=HybridSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=1000,
                chunk_overlap_tokens=100
            ),
            combination_strategy=ReciprocalRankFusionIndexCombinationStrategy(),
        ),
    )
    index = op.wait()
    print(f"Индекс {index_name} создан с первым пакетом ({len(initial_batch)} чанков)!")

    # Добавляем оставшиеся чанки пакетами
    for i in range(batch_size, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Добавление пакета {(i // batch_size) + 1} ({len(batch)} чанков)...")
        op = index.add_files_deferred(batch)
        op.wait()
        print(f"Пакет {(i // batch_size) + 1} добавлен!")

    print(f"Индекс {index_name} полностью заполнен!")
    return index


def get_files():
    """Получение списка файлов для обработки"""
    files = []

    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Add files from all data directories
    data_dirs = ['chats', 'facts', 'docs', 'institutes']
    for dir_name in data_dirs:
        dir_path = project_root / 'knowledge_base' /'data' / dir_name
        if dir_path.exists():
            files.extend(glob(str(dir_path / "*.md")))
            files.extend(glob(str(dir_path / "*.txt")))
            print(files)

    print("\nСписок файлов для обработки:")
    for file in files:
        print(f"- {file}")
    print()

    return files


def analyze_files():
    """Анализ файлов и создание поискового индекса"""
    files = get_files()
    if not files:
        print("Файлы не найдены. Проверьте пути к директориям в папке data/")
        return

    print("\nАнализ соотношения токенов и символов:")
    for file in files:
        get_token_count(file)
    print()

    # Загружаем все файлы в облако
    chunks = []
    for file in files:
        print(f"Обработка файла {file}...")
        file_chunks = chunk_and_upload_file(file)
        chunks.extend(file_chunks)
        print(f"Загружено {len(file_chunks)} чанков")

    if not chunks:
        print("Не удалось создать чанки из файлов")
        return

    # Создаём поисковый индекс
    print(f"\nСоздание поискового индекса из {len(chunks)} чанков...")
    index_id = create_and_populate_search_index(chunks, "mai_bot_index")

    # Сохраняем ID индекса
    save_search_index_id(index_id.id)
    print(f"\nПоисковый индекс {index_id} успешно создан и сохранен")


def save_search_index_id(index_id: str):
    """Сохранение ID индекса в конфигурации"""
    global env_path

    # Читаем существующий файл
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []

    # Ищем строку с SEARCH_INDEX_ID
    found = False
    for i, line in enumerate(lines):
        if line.startswith("SEARCH_INDEX_ID="):
            lines[i] = f"SEARCH_INDEX_ID={index_id}\n"
            found = True
            break

    # Если строка не найдена, добавляем новую
    if not found:
        lines.append(f"SEARCH_INDEX_ID={index_id}\n")

    # Записываем обновленный файл
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def initialize_sdk():
    """Инициализация SDK Yandex Cloud"""
    load_dotenv()

    folder_id = os.environ.get("folder_id")
    api_key = os.environ.get("api_key")

    if not folder_id or not api_key:
        raise ValueError("Не найдены необходимые переменные окружения")

    return YCloudML(folder_id=folder_id, auth=api_key)


if __name__ == "__main__":

    # Анализ файлов
    analyze_files()