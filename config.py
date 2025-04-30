from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Telegram
    bot_token: str
    password: str

    #Yandex Cloud
    api_key: str
    folder_id: str
    search_index_id: str