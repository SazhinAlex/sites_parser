from selenium import webdriver


class ChromeParser(object):
    def __init__(self, *args, **kwargs) -> None:
        options = webdriver.ChromeOptions()
        for arg in args:
            options.add_argument(arg)

        self._driver = webdriver.Chrome(options=options)

    
    def start(self, *args, **kwargs) -> None:
        raise NotImplementedError
    
