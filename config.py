from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Telegram
    bot_token: str
    admin_ids: str

    #Yandex Cloud
    api_key: str
    folder_id: str