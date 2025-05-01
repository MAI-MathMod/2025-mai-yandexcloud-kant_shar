from pydantic import BaseModel, Field
import pandas as pd
from ..telegram_bot.functions import update_user

tb = pd.read_excel('../knowledge_base/MAI_Programs.xlsx')
tb.columns = ['Code', 'Name', 'Budget-points', 'Paid-points', 'Exams', 'Faq', 'Courses']


def create_thread(sdk):
    return sdk.threads.create(ttl_days=1, expiration_policy="static")


def create_assistant(sdk, model, tools=None):
    kwargs = {}
    if tools and len(tools) > 0:
        kwargs = {"tools": tools}
    return sdk.assistants.create(
        model, ttl_days=1, expiration_policy="since_last_active", **kwargs
    )


def upload_file(sdk, filename):
    return sdk.files.upload(filename, ttl_days=1, expiration_policy="static")


class SearchProgramsList(BaseModel):
    """Функция для опрелеоения возможных направлений в вузе на основе результатов экзаменов и предпочтений.
    Одно из полей score_budget или score_paid обязательно должно быть заполнено.
    В поле exams обязательно должно быть 3 экзамена. Любой экзамен по языку кроме Русского заменяй
    на экзамен по Иностранному языку (Например, Китайский заменяй на Иностранный, с Английским,
    немецким и тп - аналогично). Если пользователь не дал информацию переспроси"""

    name: str = Field(description='Название конкурсной группы', default=None)
    code: str = Field(description='Код специальности (три числа, разделенные точками)', default=None)
    score_budget: int = Field(description='Сумма баллов за экзамены, если пользователь хочет поступить на бюджет.',
                              default=None)
    score_paid: int = Field(description='Сумма баллов за экзамены, если пользовательно хочет поступить на платное.',
                            default=None)
    exams: str = Field(description='Сданные экзамены (Математика, информатика и т.п., экзамен по родному языку - Русский).', default=None)
    sort_order: str = Field(description='Порядок выдачи (least points, medium points, most points)', default=None)

    what_to_return: str = Field(description='Что вернуть (course-info или score)', default=None)

    def process(self, thread):
        return sort_table(self)


def sort_table(req, table=tb):
    x = table.copy()
    if req.name:
        x = x[x['Name'] == req.name]
    if req.code:
        x = x[x['Code'] == req.code]
    if req.score_budget:
        x = x[x['Budget-points'] <= req.score_budget]
    if req.score_paid:
        x = x[x['Paid-points'] <= req.score_paid]
    if req.exams:
        exams = req.exams.split(', ')
        res = check_exams(x, 'Exams', exams)
        x['Contains_all_exams'] = res
        x = x[x['Contains_all_exams'] == True]
    if req.sort_order and len(x) > 0:
        if req.score_budget:
            if req.sort_order == 'least points':
                x = x.sort_values(by="Budget-points")
            elif req.sort_order == 'most points':
                x = x.sort_values(by="Budget-points", ascending=False)
        elif req.score_paid:
            if req.sort_order == 'least points':
                x = x.sort_values(by='Paid-points')
            elif req.sort_order == 'most points':
                x = x.sort_values(by='Paid-points', ascending=False)
        else:
            pass
    if x is None or len(x) == 0:
        return 'Не найдено подходящих вам направений.'
    return 'Нашлись такие направления:\n' + '\n'.join(f'{z["Code"]} - {z["Name"]} '
                                                      f'({z["Budget-points"]}/{z["Paid-points"]} '
                                                      f'бюджет/платное) с направлениями: '
                                                      f'{"".join(z["Courses"])}' for _, z in x.head(10).iterrows())


class Agent:
    def __init__(self, sdk, model, assistant=None, instruction=None, search_index=None, tools=None, chat_id=None):

        self.sdk = sdk
        self.model = model
        self.thread = None
        self.handover = False
        self.chat_id = chat_id

        if assistant:
            self.assistant = assistant
        else:
            if tools:
                self.tools = {x.__name__: x for x in tools}
                tools = [sdk.tools.function(x) for x in tools]
            else:
                self.tools = {}
                tools = []
            if search_index:
                tools.append(sdk.tools.search_index(search_index))
            self.assistant = create_assistant(sdk, model, tools)

            if instruction:
                self.assistant.update(instruction=instruction)

    def get_thread(self, thread=None):
        if thread is not None:
            return thread
        if self.thread is None:
            self.thread = create_thread(self.sdk)
        return self.thread

    def get_handover(self):
        return self.handover

    def __call__(self, message, thread=None):
        thread = self.get_thread(thread)
        thread.write(message)
        run = self.assistant.run(thread)
        res = run.wait()
        if res.tool_calls:
            result = []
            for f in res.tool_calls:
                print(
                    f" + Вызываем функцию {f.function.name}, args={f.function.arguments}"
                )
                fn = self.tools[f.function.name]
                if f.function.name == 'HandOver':
                    self.handover = True
                if f.function.name == 'SearchProgramsList':
                    search_data = fn(**f.function.arguments)
                    if search_data.exams is not None:
                        update_user(self.chat_id, 'exams', search_data.exams)
                    if search_data.score_budget is not None:
                        update_user(self.chat_id, 'score', search_data.score_budget)
                        update_user(self.chat_id, 'department', 'budget')
                    if search_data.score_paid is not None:
                        update_user(self.chat_id, 'score', search_data.score_paid)
                        update_user(self.chat_id, 'department', 'paid')
                obj = fn(**f.function.arguments)
                x = obj.process(thread)
                result.append({"name": f.function.name, "content": x})
            run.submit_tool_results(result)
            res = run.wait()
        return res.text

    def restart(self):
        if self.thread:
            self.thread.delete()
            self.thread = self.sdk.threads.create(
                name="Test", ttl_days=1, expiration_policy="static"
            )

    def done(self, delete_assistant=False):
        if self.thread:
            self.thread.delete()
        if delete_assistant:
            self.assistant.delete()


def check_exams(df: pd.DataFrame, column_name: str, exams):
    results = []

    for cell in df[column_name]:
        expr = [1 for exam in exams if exam.lower() in cell.lower()]
        if len(expr) >= 3:
            results.append(True)
        else:
            results.append(False)

    return results


class HandOver(BaseModel):
    """Эта функция предназначена для перевода твеого диалога с пользователем на диалог с человеком-оператором"""

    def process(self, thread):


        return 'Подождите немного, оператор скоро придет и поможет вам решить вашу проблему!'