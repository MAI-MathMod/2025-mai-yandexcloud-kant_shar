import json
from pathlib import Path
import pymysql
# from assistant.funcs import *
# from assistant.assistant import *


def save_user(user_id, user_nick, role = 'user'):
    try:
        user_query = """
            INSERT INTO users_for_yandex(user_id, user_nick, role, ball, exams)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(user_query, (user_id, user_nick, role, '0', '0'))
        connection.commit()
        return 'success'

    except pymysql.MySQLError as e:
        connection.rollback()
        return f"Ошибка подключения: {e}"


def update_user_role(user_id: int, new_role: str):
    """
    Изменяет роль пользователя по его уникальному идентификатору.
    Аргументы:
        user_id: уникальный идентификатор пользователя
        new_role: новая роль пользователя
    Возвращает:
        bool: True, если роль была успешно изменена, иначе False
    """
    try:
        query = "UPDATE users_for_yandex SET role = %s WHERE user_id = %s"
        cursor.execute(query, (new_role, str(user_id)))
        connection.commit()
        return True
    except pymysql.MySQLError as e:
        connection.rollback()
        raise f"Ошибка подключения: {e}"


def get_all_admin_ids():
    """
    Возвращает список всех ID пользователей с ролью 'admin'.
    Возвращает:
        list: список всех ID администраторов
    """
    cursor.execute('SELECT user_id FROM users_for_yandex WHERE role = "admin"')
    result = cursor.fetchall()
    result = [i[0] for i in result]
    return result


def stay_in_quire(user_id):
    file_path = '../telegram_bot_data/callstack.json'
    file = Path(file_path)

    data = {}
    if file.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла: {e}")
            data = {}
    if any(user_id == i for i in data['queue']):
        return data['queue'].index(user_id) + 1
    data['queue'].append(user_id)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        raise IOError(f"Ошибка при записи данных в файл '{file_path}': {e}")


def create_dialog(admins_id):
    file_path = '../telegram_bot_data/callstack.json'
    file = Path(file_path)

    data = {}
    if file.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла: {e}")
            data = {}

    for dialog in data.get('dialogs', []):
        if admins_id in dialog:
            return False

    if not data.get('queue'):
        return False

    dialog = [data['queue'][0], admins_id]
    if 'dialogs' not in data:
        data['dialogs'] = []
    data['dialogs'].append(dialog)
    del data['queue'][0]

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        raise IOError(f"Ошибка при записи данных в файл '{file_path}': {e}")


def get_visavi(user_id):
    file_path = '../telegram_bot_data/callstack.json'
    file = Path(file_path)

    data = {}
    if file.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла: {e}")
            return False
    for dialog in data['dialogs']:
        if dialog[0] == user_id:
            return dialog[1]
        if dialog[1] == user_id:
            return dialog[0]
    return False


def stop_dialog(user_id):
    file_path = '../telegram_bot_data/callstack.json'
    file = Path(file_path)

    data = {}
    if file.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла: {e}")
            data = {}

    if 'dialogs' not in data:
        data['dialogs'] = []

    dialog_index = None
    for i, dialog in enumerate(data['dialogs']):
        if user_id in dialog:
            dialog_index = i
            break

    if dialog_index is not None:
        del data['dialogs'][dialog_index]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except IOError as e:
            raise IOError(f"Ошибка при записи данных в файл '{file_path}': {e}")
    return False

def get_or_create_assistant(assistants: dict, user_id: int):
    if user_id in assistants:
        return assistants[user_id]
    assistants[user_id] = Agent(sdk=sdk, model=model, instruction=instruction, search_index=search_index,
                                tools=[SearchProgramsList, HandOver])
    return assistants[user_id]


def clear_assistants(assistants, user_id):
    if user_id in assistants:
        try:
            assistants[user_id].done()
            del assistants[user_id]
        except Exception as e:
            print(e)


def reset_user_handover(user_id):
    file_path = '../telegram_bot_data/callstack.json'


with open('../telegram_bot_data/database_user.json') as file:
    file_json_data = json.load(file)
try:
    connection = pymysql.connect(
        host=file_json_data['host'],
        user=file_json_data['user'],
        password=file_json_data['password'],
        database=file_json_data['database']
    )
    cursor = connection.cursor()
    print(get_all_admin_ids())
except pymysql.MySQLError as e:
    print(f"Ошибка подключения: {e}")