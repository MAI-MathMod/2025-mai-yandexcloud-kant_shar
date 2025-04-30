from pydantic import BaseModel, Field
from typing import Optional


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
    """Функция для опрелеоения возможных направлений в вузе на основе результатов экзаменов и предпочтений."""

    name: str = Field(description='Название конкурсной группы', default=None)
    code: str = Field(description='Код специальности (три числа, разделенные точками)', default=None)
    score: str = Field(description='Сумма баллов за экзамены', default=None)
    exams: str = Field(description='Сданные экзамены (Математика, информатика и т.п.)', default=None)
    sort_order: str = Field(description='Порядок выдачи (least points, medium points, most points)', default=None)

    what_to_return: str = Field(description='Что вернуть (course-info или score)', default=None)