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

op = sdk.search_indexes.create_deferred(
    upload_file(sdk, '../knowledge_base/programs_table.md'),
    index_type=HybridSearchIndexType(
        chunking_strategy=StaticIndexChunkingStrategy(
            max_chunk_size_tokens=1500, chunk_overlap_tokens=100
        ),
        combination_strategy=ReciprocalRankFusionIndexCombinationStrategy(),
    ),
)
index = op.wait()

search_tool = sdk.tools.search_index(index)
table_search_tool = sdk.tools.function(SearchProgramsList)

assistant = create_assistant(sdk, model, tools=[table_search_tool])

thread = create_thread(sdk)
assistant.update(instruction="""Ты сотрудник приемной комиссии Московского Авиационного Института (МАИ). 
Твоя задача консультировать абитуриентов по вопросам по поводу поступления или самого института, а также определять, 
может ли абитуриент поступить на какое-либо направление. Когда пользователь спрашивает, на какие направления в МАИ он 
может поступить, вызывай функцию SearchProgramsList. Посмотри на всю имеющуюся в твоем распоряжении информацию
и сделай самый понятный и достоверный ответ. Не упоминай, что что-то можно уточнить в приемной комиссии. 
Если что-то непонятно - переспроси""")

thread.write('Куда я могу поступить имея 265 баллов? Я сдавал математику, информатику и русский')
run = assistant.run(thread)
res = run.wait()
print(res)

