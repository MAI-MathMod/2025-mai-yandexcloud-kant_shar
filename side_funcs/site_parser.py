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
    programs[-1]['points'] = f'{points[0]}/{points[1]}'
    places = needed_div.div.find_all('span')[7].span.text.strip().split('/')
    programs[-1]['places'] = f"{places[0]}/{places[1].replace('\n', '').replace(' ', '')}"
    exams = needed_div.find_all('span')[3].text.strip().split(' ')
    programs[-1]['subjects'] = (f'{exams_converter[exams[0]]}, и {exams_converter[exams[2]]}, '
                                f'и {exams_converter[exams[1].split('/')[0]]} или '
                                f'{exams_converter[exams[1].split('/')[1]]}')

    i = 0
    for sibling in needed_div.div.next_siblings:
        if i % 2 and i <= 62:
            programs.append(dict())
            programs[-1]['name'] = sibling.find('h3').text.strip()
            code = sibling.find('span', class_='program-codes mb-lg-0 mb-3').text.strip()
            if i in [29, 51]:
                programs[-1]['code'] = (f'{code[:len(code) // 2]} '
                                        f'({code[len(code) // 2:]})')
            else:
                programs[-1]['code'] = code
            points = sibling.find('span', class_='program-points').span.text.strip().split('/')
            programs[-1]['points'] = f'{points[0]}/{points[1]}'
            if i in [35, 37, 41, 51, 57, 59]:
                places = sibling.div.find_all('span')[8].span.text.strip().split('/')
            else:
                places = sibling.div.find_all('span')[7].span.text.strip().split('/')
            if i in [29, 51]:
                places_paid = places[1].replace('\n', '').replace(' ', '')
                number = places_paid.split('\xa0')[-1]
                programs[-1]['places'] = (f'{places[0]}/{places_paid[:places_paid.rindex(number)]} '
                                          f'({places_paid[places_paid.rindex(number):]})')
            else:
                programs[-1]['places'] = f"{places[0]}/{places[1].replace('\n', '').replace(' ', '')}"
            exams = sibling.find_all('span')[3].text.strip().split(' ')
            programs[-1]['subjects'] = (f'{exams_converter[exams[0]]}, и {exams_converter[exams[2]]}, '
                                        f'и {exams_converter[exams[1].split('/')[0]]} или '
                                        f'{exams_converter[exams[1].split('/')[1]]}')
        i += 1

    table_header = (f'|Код|Наименование конкурсной группы|Кол-во мест (бюджет / платное)|Баллы (бюджет / платное)|Необходимые редметы '
                    f'для поступления|\n'
                    f'|:-:|:----------------------------:|:--------------------------:|:--------------------:|:---------'
                    f'-------------:|\n')
    table = ''
    for program in programs:
        table = (f'{table}|{program["code"]}|{program["name"]}|{program["places"]}|{program['points']}|'
                 f'{program['subjects']}|\n')

    table = f'{table_header}{table}'

    return table, table_header


def generate_md_file(text: str):
    with open('./knowledge_base/programs_table.md', 'w', encoding='utf-8') as f:
        f.write(text)