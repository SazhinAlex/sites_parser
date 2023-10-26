from sites_parser import ChromeParser, check_folder_create
from pathlib import Path
from time import time, sleep
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests


class LamodaParser(ChromeParser):
    def __init__(self, *args, **kwargs) -> None:
        chrome_options =(
            '--disable-infobars',
            '--headless',
            '--ignore-certificate-errors',
            '--no-first-run',
            '--log-level=3',
            '--ignore-certificate-errors-spki-list'
        )
        super().__init__(*chrome_options)

        self.__lamoda_url_w = 'https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/'
        self.__lamoda_url_base = 'https://www.lamoda.ru'
        self.__lamoda_menu_xpath = "//div[@id='catalog-main']/div[1]/div[1]/div[1]/div[2]/ul[1]"
        # self.__mlink_active_class = "router-link-exact-active"
        # self.__arrow_class = 'ui-catalog-tree-arrow-icon-level-2'
        self.__delay_s = 3
        self.__img_dowloaded = 0
        self.__bad_img = 0
        self.__started = None
        self.__finished = None
        self.__output_dir = check_folder_create(Path(__file__).parent / 'output')



    def __get_menu_tag_list(self, *args, **kwargs) -> tuple:
        content = self._driver.find_element(By.XPATH, self.__lamoda_menu_xpath)
        lst = content.find_elements(By.TAG_NAME, 'a')
        result = ((a.text, a.get_dom_attribute('href')) for a in lst)
        return tuple(result)
    
    def __get_inner_menu_links(self, active_link: tuple, *args, **kwargs) -> tuple:
        inner_ul_xpath = f"//a[@router-link-exact-active | @href='{active_link[1]}']" \
            "/ancestor::li[1]/descendant::ul/descendant::a"
        
        result = self._driver.find_elements(By.XPATH, inner_ul_xpath)
  
        result = (((a.text, a.get_dom_attribute('href')) for a in result))

        return tuple(result)
    
    def __download(self, save_path: Path, *args, **kwargs):
        forward_xpath = "//div[text()='Дальше']/ancestor::a[contains(@class," \
            "'router-link-active')]"
        
        while True:
            sleep(self.__delay_s)
            card_img_xpath = "//img[contains(@class, 'x-product-card__pic-img')]" 
                
            img_elements = self._driver.find_elements(By.XPATH, card_img_xpath)
            for img_elem in img_elements:
                img_url = img_elem.get_dom_attribute('src')
                img_url = 'https:' + img_url
                resp = requests.get(img_url)
                if not resp.ok:
                    self.__bad_img += 1
                    continue
                img_file_name = img_url.split('/')[-1]
                img_file_path = save_path / img_file_name
                with open(img_file_path, 'wb') as file:
                    file.write(resp.content)
                self.__img_dowloaded += 1

            try:
                forward_a = self._driver.find_element(By.XPATH, forward_xpath)
            except NoSuchElementException:
                break
            
            forward_link = forward_a.get_dom_attribute('href')
            self._driver.get(self.__lamoda_url_base + forward_link)


    def __rwalk(self, l: tuple, t_pth=None, *args, **kwargs):
        sleep(self.__delay_s)
        for li in l:
            go_to_link = self.__lamoda_url_base + li[1]
            self._driver.get(go_to_link)
            print(f'Log: Transition to {go_to_link}')
            save_pth = self.__output_dir / li[0] if not t_pth else t_pth / li[0]
            save_pth = check_folder_create(save_pth)
            inner_ul = self.__get_inner_menu_links(li)
            if len(inner_ul) > 0:

                self.__rwalk(inner_ul, save_pth)
            else:
                self.__download(save_pth)

    def start(self, *args, **kwargs) -> None:
        self.__started = time()
        self.__output_dir = self.__output_dir / f'output_{int(time() * 1000)}'
        self.__output_dir = check_folder_create(self.__output_dir)
        self._driver.get(self.__lamoda_url_w)
        cat_list = self.__get_menu_tag_list()
        self.__rwalk(l=cat_list)
        self.__finished = time()
        print('Finished!')
