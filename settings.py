from pydantic import BaseModel, Field
from pathlib import Path


class Settings(BaseModel):
    BASE_URLS: list[str] = [
        "https://pastvu.com/ps/1?f=r%21471",
    ]
    SLOW_MO: int = Field(default=1, ge=1)
    ITEMS_PER_PAGE: int = 10
    RELATIVE_STORAGE_FOLDER: str = "images"
    HEADLESS: bool = False

    @property
    def STORAGE_FOLDER(self) -> Path:
        return Path.cwd() / self.RELATIVE_STORAGE_FOLDER


settings = Settings()
