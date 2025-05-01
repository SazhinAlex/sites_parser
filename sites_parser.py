import undetected_chromedriver as uc
from pathlib import Path
import requests
from time import sleep, time


def try_request(url: str, retry_time = 120.0, retries = 5000) -> requests.Response:
    err_text = 'Не удалось получить данные с '
    responce = None
    counter = 0
    while not responce and counter < retries:
        try:
            responce = requests.get(url,timeout=30)
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
        options = uc.ChromeOptions()
        #options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #options.add_experimental_option('useAutomationExtension', False)
        for arg in args:
            options.add_argument(arg)

        #self._driver = webdriver.Chrome(options=options)
        self._driver = uc.Chrome()
        
        #self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        #self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'})
        self._driver.set_page_load_timeout(30)

    
    def start(self, *args, **kwargs) -> None:
        raise NotImplementedError
    

class PExeption(Exception):
    def __init__(self, etext = 'Ошибка! Возможно структура сайта была изменена...') -> None:
        super().__init__(etext)
    

output_dir = check_folder_create(Path(__file__).parent / 'output')