---

### To Run :
- Python and pip required.

- python -m venv .venv

- Activate virtual environment:
    - For Windows: .venv\Scripts\activate
	- For Linux: .venv/bin/activate

- pip install -r requirements.txt

- Adjust settings in settings.py -> Settings

- python main.py to run

---

### Settings :
- BASE_URLS: list of initial urls

- SLOW_MO: delay before each get request

- ITEMS_PER_PAGE: how much links to extract to go to

- RELATIVE_STORAGE_FOLDER: relative path to folder where files to storage

- HEADLESS: set True to hide webdriver
---
