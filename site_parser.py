import bs4, requests


def get_last_year_scores(url='https://priem.mai.ru/base/score/') -> tuple[str, str]:
    page = requests.get(url)
    soup = bs4.BeautifulSoup(page.text, 'html.parser')

    table = soup.find_all('table')[3]
    table_content = table.find_all('td')

    scores = []
    num = 0
    for i in range(0, 78, 3):
        scores.append(dict())
        scores[num]['code'] = table_content[i].text.strip().replace('\xa0', ' ')
        scores[num]['name'] = table_content[i + 1].text.strip().replace('\xa0', ' ')
        scores[num]['score'] = table_content[i + 2].text.strip().replace('\xa0', ' ')
        num += 1

    table_header = (f'|Код|Наименование конкурсной группы|Минимальный балл|\n'
                    f'|:-:|:----------------------------:|:--------------:|\n')
    table = ''
    for score in scores:
        table = f'{table}|{score["code"]}|{score["name"]}|{score["score"]}|\n'

    table = f'{table_header}{table}'

    return table, table_header


def generate_md_file(text: str):
    with open('scores_table.md', 'w', encoding='utf-8') as f:
        f.write(text)
