import bs4, requests
from os import getcwd


def get_last_year_programs(url='https://priem.mai.ru/base/programs/') -> tuple[str, str]:
    exams_converter = {
        'M': 'Математика',
        'Ф': 'Физика',
        'И': 'Информатика',
        'Б': 'Биология',
        'Г': 'География',
        'О': 'Обществознание',
        'Ин': 'Иностранный язык',
        'Ис': 'История',
        'Р': 'Русский язык'
    }
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.text, 'html.parser')

    i = 0
    for sibling in soup.find_all('div')[21].find('div').find('div').find('div').find('div').next_siblings:
        if i == 13:
            needed_div = sibling
            break
        i += 1

    programs = [dict()]
    programs[-1]['name'] = needed_div.div.find('h3').text.strip()
    programs[-1]['code'] = needed_div.div.find('span', class_='program-codes mb-lg-0 mb-3').text.strip()
    points = needed_div.find('span', class_='program-points').span.text.strip().split('/')
    programs[-1]['points-budget'] = points[0].replace('\xa0', '')
    programs[-1]['points-paid'] = points[1].replace('\xa0', '')
    exams = needed_div.find_all('span')[3].text.strip().split(' ')
    programs[-1]['subjects'] = (f'{exams_converter[exams[0]]}, и {exams_converter[exams[2]]}, '
                                f'и {exams_converter[exams[1].split('/')[0]]} или '
                                f'{exams_converter[exams[1].split('/')[1]]}')

    i = 0
    for sibling in needed_div.div.next_siblings:
        if i % 2 and i <= 62:
            sec_dict = {}
            programs.append(dict())
            programs[-1]['name'] = sibling.find('h3').text.strip()
            code = sibling.find('span', class_='program-codes mb-lg-0 mb-3').text.strip()
            points = sibling.find('span', class_='program-points').span.text.strip().split('/')
            programs[-1]['points-budget'] = points[0].replace('\xa0', '')
            programs[-1]['points-paid'] = points[1].replace('\xa0', '')
            if i in [29, 51]:
                programs[-1]['code'] = code[:len(code) // 2]
                sec_dict['code'] = code[len(code) // 2:]
                sec_dict['name'] = programs[-1]['name']
                sec_dict['points-budget'] = programs[-1]['points-budget']
                sec_dict['points-paid'] = programs[-1]['points-paid']
                exams = sibling.find_all('span')[3].text.strip().split(' ')
                programs[-1]['subjects'] = (f'{exams_converter[exams[0]]}, и {exams_converter[exams[2]]}, '
                                            f'и {exams_converter[exams[1].split('/')[0]]} или '
                                            f'{exams_converter[exams[1].split('/')[1]]}')
                sec_dict['subjects'] = programs[-1]['subjects']
                programs.append(sec_dict)
            else:
                programs[-1]['code'] = code
                exams = sibling.find_all('span')[3].text.strip().split(' ')
                programs[-1]['subjects'] = (f'{exams_converter[exams[0]]}, и {exams_converter[exams[2]]}, '
                                            f'и {exams_converter[exams[1].split('/')[0]]} или '
                                            f'{exams_converter[exams[1].split('/')[1]]}')
        i += 1

    table_header = (f'|Код|Наименование конкурсной группы|Баллы на бюджет|Баллы на платное|Необходимые предметы '
                    f'для поступления|\n'
                    f'|:-:|:----------------------------:|:-------------:|:--------------:|:--------------------'
                    f'--------------:|\n')
    table = ''
    for program in programs:
        table = (f'{table}|{program["code"]}|{program["name"]}|{program["points-budget"]}|{program['points-paid']}|'
                 f'{program['subjects']}|\n')

    table = f'{table_header}{table}'

    return table, table_header


def generate_md_file(text: str):
    with open('./knowledge_base/programs_table.md', 'w', encoding='utf-8') as f:
        f.write(text)