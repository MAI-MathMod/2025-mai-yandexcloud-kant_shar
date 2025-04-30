from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Telegram
    bot_token: str
    admin_ids: str
    password: str

    #Yandex Cloud
    api_key: str
    folder_id: str