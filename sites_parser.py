from selenium import webdriver
from pathlib import Path
import requests
from time import sleep, time


def try_request(url: str, retry_time = 5.0, retries = 5) -> requests.Response:
    err_text = 'Не удалось получить данные с '
    responce = None
    counter = 0
    while not responce and counter < retries:
        try:
            responce = requests.get(url)
        except requests.RequestException:
            print(f'{err_text}{url}. Ждем {retry_time} сек. и пробуем снова...')
        if not responce or not responce.ok:
            sleep(retry_time)
        counter += 1
    if responce is None: 
        raise PExeption(f'Не удалось получить данные с {url}')
    
    return responce


def check_folder_create(pth: Path) -> Path:
    if not pth.is_dir() or not pth.exists():
        pth.mkdir()

    return pth


class ChromeParser(object):
    def __init__(self, *args, **kwargs) -> None:
        options = webdriver.ChromeOptions()
        for arg in args:
            options.add_argument(arg)

        self._driver = webdriver.Chrome(options=options)
        self._driver.set_page_load_timeout(120)

    
    def start(self, *args, **kwargs) -> None:
        raise NotImplementedError
    

class PExeption(Exception):
    def __init__(self, etext = 'Ошибка! Возможно структура сайта была изменена...') -> None:
        super().__init__(etext)
    

output_dir = check_folder_create(Path(__file__).parent / 'output')