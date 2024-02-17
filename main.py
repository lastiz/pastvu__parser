from pathlib import Path
from typing import Self
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import requests
import shutil
import urllib3
from datetime import datetime
from time import sleep
from pathvalidate import sanitize_filename

from settings import settings
from logger import logger


class ScraperError(Exception):
    pass


class Downloader:
    _STORAGE_FOLDER = settings.STORAGE_FOLDER

    def __init__(self) -> None:
        if not self._STORAGE_FOLDER.is_dir():
            self._STORAGE_FOLDER.mkdir()

    def dowload_file(self, src: str) -> requests.Response | None:
        logger.info(f"Starting download file {src}")
        try:
            response = requests.get(src, stream=True)
        except BaseException:
            logger.error(f"Failed to load file {src}")
            return

        if not response.ok:
            logger.error(f"Failed to load file {src}")
            return

        return response

    def sanitize_filename(self, path) -> str:
        return sanitize_filename(path)

    def build_full_filename(self, filename: str, extension: str) -> Path | str:
        """Builds full filename path
            If filename already exists - adds utc-time to filename

        Args:
            filename (str): filename without extension
            extension (str): extension

        Returns:
            Path: fqdn for file
        """
        sanitized_filename = self.sanitize_filename(f"{filename}.{extension}")
        path = self._STORAGE_FOLDER / sanitized_filename
        if path.is_file():
            path = self._STORAGE_FOLDER / self.sanitize_filename(
                f"{filename}-{datetime.utcnow()}.{extension}"
            )

        return path

    def save_file(self, filename: str, src: str) -> None:
        extension = src.split(".")[-1]

        file_response = self.dowload_file(src)
        if not file_response:
            return

        file_full_path = self.build_full_filename(filename, extension)

        logger.info(f"Saving file {file_full_path}")
        try:
            with open(file_full_path, "wb") as f:
                file_response.raw.decode_content = True
                shutil.copyfileobj(file_response.raw, f)
        except:
            logger.error(f"Failed to save file {file_full_path}")
        logger.info(f"Completed saving file {file_full_path}")


class Scraper:
    _slowMo = settings.SLOW_MO
    _session = None
    _base_urls = settings.BASE_URLS
    _user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    _items_per_page = settings.ITEMS_PER_PAGE

    def __init__(self) -> None:
        self.downloader = Downloader()

    @property
    def session(self):
        if self._session is None:
            raise ScraperError("Driver wasn't initialized")
        return self._session

    def __enter__(self) -> Self:
        chrome_options = Options()
        chrome_options.add_argument(f"--user-agent={self._user_agent}")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        if settings.HEADLESS:
            chrome_options.add_argument("--headless")

        self._session = webdriver.Chrome(options=chrome_options)
        return self

    def __exit__(self, *args, **kwargs) -> None:
        self.session.close()

    @property
    def user_agent(self) -> str:
        return self._user_agent

    @user_agent.setter
    def user_agent(self, val: dict) -> None:
        if not isinstance(val, str):
            raise TypeError("User Agent value must be a string")
        self._user_agent = val

    def get(self, url: str) -> None:
        """Get driver to :url"""
        try:
            self.session.get(url)
        except BaseException:
            logger.error(f"Failed to get to this URL {url}")

        logger.info(f"Going to {url}")
        sleep(self._slowMo)

    def find_elements_by_class(self, class_: str) -> list[WebElement]:
        """Finds elements by :class_"""
        return self.session.find_elements(By.CLASS_NAME, class_)

    def get_href_from_elements(
        self,
        link_elements: list[WebElement],
        link_amount: int | None = None,
        base_url: str | None = None,
    ) -> list[str]:
        """Gets hrefs from elements"""
        if link_amount is None:
            link_amount = self._items_per_page
        res = []
        for el in link_elements[:link_amount]:
            href = self.get_href_from_element(el, base_url=base_url)
            if not href is None:
                res.append(href)
        return res

    def get_href_from_element(
        self,
        element: WebElement,
        base_url: str | None = None,
    ) -> str | None:
        "Gets href from :element"
        href = element.get_attribute("href")
        if not href is None:
            if base_url:
                href = self.build_abs_url(
                    host=urllib3.util.parse_url(base_url),  # type: ignore
                    path=href,
                )

            logger.info(f"Extracted link - {href}")
            return href

    def get_src_from_element(
        self, element: WebElement, base_url: str | None = None
    ) -> str | None:
        src = element.get_attribute("src")
        if not src is None:
            if base_url:
                src = self.build_abs_url(
                    host=urllib3.util.parse_url(base_url),  # type: ignore
                    path=src,
                )

            logger.info(f"Extracted IMAGE link - {src}")
            return src

        logger.error(f"Failed to extract IMAGE link in page {base_url}")

    def find_element_by_class(self, class_) -> WebElement:
        "Finds element by :class_"
        return self.session.find_element(By.CLASS_NAME, class_)

    def find_element_by_classes(self, tag_name: str, classes: str) -> WebElement:
        """Finds elements by classes

        Args:
            tag_name (str): TAG in HTML
            classes (str): Classes written in "class1 class2" manner

        Returns:
            WebElement: WebElement
        """
        return self.session.find_element(By.XPATH, f"//{tag_name}[@class='{classes}']")

    def get_text_from_element(self, element: WebElement) -> str:
        return element.text

    def build_abs_url(self, host: str, path: str, scheme: str = "https") -> str:
        if path.startswith("/"):
            return f"{scheme}://{host}/{path}"
        return path

    def crawl(self) -> None:
        for base_url in self._base_urls:
            self.get(base_url)
            elements_to_go = self.find_elements_by_class("photoBox")
            links_to_go = self.get_href_from_elements(elements_to_go, base_url=base_url)
            for link in links_to_go:
                self.get(link)

                # Searhing title date and image link to save file
                title_element = self.find_element_by_classes("div", "info title")
                file_title = self.get_text_from_element(title_element)
                date_element = self.find_element_by_classes(
                    "span", "tltp-wrap rytltp-wrap"
                )
                file_date = self.get_text_from_element(date_element)
                file_element = self.find_element_by_class(class_="photoImg")
                file_link = self.get_src_from_element(file_element, base_url=link)

                if file_link:
                    self.downloader.save_file(
                        filename=f"{file_title}-{file_date}",
                        src=file_link,
                    )


if __name__ == "__main__":
    with Scraper() as scraper:
        scraper.crawl()
