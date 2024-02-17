from pydantic import BaseModel
from pathlib import Path


class Settings(BaseModel):
    BASE_URLS: list[str] = [
        "https://pastvu.com/ps/1?f=r%21471",
    ]
    SLOW_MO: int = 1
    ITEMS_PER_PAGE: int = 15
    RELATIVE_STORAGE_FOLDER: str = "images"

    @property
    def STORAGE_FOLDER(self) -> Path:
        return Path.cwd() / self.RELATIVE_STORAGE_FOLDER


settings = Settings()
