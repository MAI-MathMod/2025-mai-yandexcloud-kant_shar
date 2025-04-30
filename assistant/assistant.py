from yandex_cloud_ml_sdk import YCloudML
from config import Config
from funcs import *
from yandex_cloud_ml_sdk.search_indexes import (
    StaticIndexChunkingStrategy,
    HybridSearchIndexType,
    ReciprocalRankFusionIndexCombinationStrategy,
)


config = Config(_env_file='../.env')
sdk = YCloudML(folder_id=config.folder_id, auth=config.api_key)
model = sdk.models.completions("yandexgpt", model_version="rc")

instruction="""Ты сотрудник приемной комиссии Московского Авиационного Института (МАИ). 
Твоя задача консультировать абитуриентов по вопросам по поводу поступления или самого института, а также определять, 
может ли абитуриент поступить на какое-либо направление. Когда пользователь спрашивает, на какие направления в МАИ он 
может поступить, вызывай функцию SearchProgramsList. Посмотри на всю имеющуюся в твоем распоряжении информацию
и сделай самый понятный и достоверный ответ. Не упоминай, что что-то можно уточнить в приемной комиссии. 
Если что-то непонятно - переспроси"""

priem_agent = Agent(sdk=sdk, model=model, instruction=instruction, tools=[SearchProgramsList])
print(priem_agent('Привет! Куда я могу поступить в МАИ?'))
print(priem_agent('Я сдавал информатику и математику'))
print(priem_agent('А точно, я еще сдавал русский'))
print(priem_agent('Я набрал 265 баллов, хотелось бы на бюджет. Можешь предоставить результат в порядке убывания?'))