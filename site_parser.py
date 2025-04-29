import bs4, requests


def get_last_year_programs(url='https://priem.mai.ru/base/programs/') -> tuple[str, str]:
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
    programs[-1]['subjects'] = needed_div.div.find_all('span')[3].text.strip()

    i = 0
    for sibling in needed_div.div.next_siblings:
        if i % 2 and i <= 62:
            programs.append(dict())
            programs[-1]['name'] = sibling.find('h3').text.strip()
            programs[-1]['code'] = sibling.find('span', class_='program-codes mb-lg-0 mb-3').text.strip()
            points = sibling.find('span', class_='program-points').span.text.strip().split('/')
            programs[-1]['points'] = f'{points[0]}/{points[1]}'
            if i in [35, 37, 41, 51, 57, 59]:
                places = sibling.div.find_all('span')[8].span.text.strip().split('/')
            else:
                places = sibling.div.find_all('span')[7].span.text.strip().split('/')
            programs[-1]['places'] = f"{places[0]}/{places[1].replace('\n', '').replace(' ', '')}"
            programs[-1]['subjects'] = sibling.find_all('span')[3].text.strip()
        i += 1

    table_header = (f'|Код|Наименование конкурсной группы|Кол-во мест (платное/бюджет)|Баллы (платное/бюджет)|Предметы '
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
    with open('programs_table.md', 'w', encoding='utf-8') as f:
        f.write(text)

