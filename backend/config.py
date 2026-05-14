from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # 百川
    baichuan_api_key: str = ""
    baichuan_base_url: str = "https://api.baichuan-ai.com"

    # Chroma
    chroma_persist_dir: str = "../data/chroma_db"

    # 应用
    app_title: str = "初中物理知识检索系统"
    app_version: str = "1.0.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
