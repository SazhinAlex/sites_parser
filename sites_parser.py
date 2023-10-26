from selenium import webdriver
from pathlib import Path
    

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

    
    def start(self, *args, **kwargs) -> None:
        raise NotImplementedError
    
