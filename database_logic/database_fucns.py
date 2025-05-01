import json
import pymysql


def update_user(user_id, column, new_value):
    try:
        query = f"UPDATE users_for_yandex SET `{column}` = %s WHERE user_id = %s"
        valid_columns = ['user_id', 'user_nick', 'role',
                         'score', 'department', 'exams', 'distribution']
        if column not in valid_columns:
            return False
        cursor.execute(query, (new_value, user_id))
        connection.commit()
        return True
    except pymysql.MySQLError as e:
        connection.rollback()
        raise f"Ошибка подключения: {e}"


def save_user(user_id, user_nick, role = 'user'):
    try:
        user_query = """
            INSERT INTO users_for_yandex(user_id, user_nick, role, score, department, exams, distribution)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(user_query, (user_id, user_nick, role, '0', '0', '0', 0))
        connection.commit()
        return 'success'

    except pymysql.MySQLError as e:
        connection.rollback()
        return f"Ошибка подключения: {e}"


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



def get_distribution():
    cursor.execute('SELECT user_id FROM users_for_yandex WHERE distribution = 1')
    result = cursor.fetchall()
    result = [i[0] for i in result]
    return result


def get_all():
    cursor.execute('SELECT * FROM users_for_yandex')
    result = cursor.fetchall()
    for i in result:
        print(i)


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
except pymysql.MySQLError as e:
    print(f"Ошибка подключения: {e}")