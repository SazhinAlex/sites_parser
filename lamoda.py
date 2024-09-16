from sites_parser import ChromeParser, try_request, PExeption, output_dir, check_folder_create
from pathlib import Path
from time import time, sleep
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from lxml import etree
from db import LamodaItem, Base
import os
import sys



downloaded = 0
desc_xpath = "//span[ancestor::div[contains(@class, '_description_') and ancestor::div[contains(@id, 'reviews-and-questions')]]]"
img_xpath = "//img[contains(@class, '_image_1') and ancestor::div[contains(@class, 'ui-product-page-gallery')]]"
promo2_close = "//div[@title='Закрыть' and contains(@class, 'icon_cross-thin-white') and ancestor::div[@class='d-modal__close-button']]"
lamoda_url_w = 'https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/'
card_link = "//a[@role='link' and contains(@class, 'x-product-card__pic-catalog')]"
forward_xpath = "//a[contains(@class, 'router-link-active') and descendant::div[text()='Дальше']]"
sub_arrow = ".//div[contains(@class, 'ui-catalog-tree-arrow-icon-level-2')]"

run = False



def links_to_dict(links: list[WebElement]) -> dict:
    if len(links) == 0:
        raise ValueError('Пустой список недопустим!')
    result = {}
    for link in links:
        result[link.text.strip()] = link.get_attribute('href')
    
    return result


def selenium_to_file(web_driver, print_info = True):
    filename = f'dump_{int(time() * 1000)}.txt'
    with open(filename, 'w', encoding='utf8') as file:
        file.write(BeautifulSoup(web_driver.page_source, 'html5lib').prettify())
    if print_info:
        print(f'Сохранено: {filename}')



def try_webdriver_get(url: str, driver: webdriver.Chrome, fail_wait = 120.0, limit = 5000):
    counter = 0
    while counter < limit:
        try:
            driver.get(url)
            break
        except Exception:
            counter += 1
            if counter == limit:
                raise PExeption(f'После {counter} попыток не удалось получить данные с {url} Работа завершена.')
            sleep(fail_wait)


def etree_from_driver(driver: webdriver.Chrome):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return etree.HTML(str(soup))


def get_etree_html(url: str, driver: webdriver.Chrome, fail_wait = 5.0, limit = 5):
    try_webdriver_get(url, driver, fail_wait, limit)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return etree.HTML(str(soup))


def get_card_data(url: str, save_pth: Path, driver: webdriver.Chrome) -> LamodaItem|None:
    try_webdriver_get(url, driver)
    
    promo = driver.find_elements(By.XPATH, promo2_close)
    if len(promo) > 0:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, promo2_close))).click()
    try:
        imgs = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, img_xpath)))
    except TimeoutException:
        return None
    img_url = imgs[0].get_attribute('src')

    item = LamodaItem()

    item.prod_url = url
    item.img_url = img_url
    try:
        item.materials = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-material_filling')]"
            ).text
    except NoSuchElementException:
        item.materials = ''

    try:
        item.size_on_model = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-correspond_to_size')]"
            ).text
    except NoSuchElementException:
        item.size_on_model = ''

    try:
        item.model_params = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-model_parameters')]"
            ).text
    except NoSuchElementException:
        item.model_params = ''

    try:            
        item.model_heigh = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-model_height_on_photo')]"
            ).text
    except NoSuchElementException:
        item.model_heigh = ''

    try:
        item.lenght = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-length')]"
            ).text
    except NoSuchElementException:
        item.lenght = ''

    try:
        item.season = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-season_wear')]"
            ).text
    except NoSuchElementException:
        item.season = ''

    try:
        item.color = driver.find_element(
            By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-color_family')]"
            ).text
    except NoSuchElementException:
        item.color = ''

    
    try:
        price = driver.find_element(By.XPATH, "//span[contains(@aria-label, 'Итоговая цена')]")
        item.price = price.text.strip()
    except Exception:
        item.price = ''

    
    try:
        sku = driver.find_element(By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-sku')]")
        item.sku = sku.text.strip()
    except Exception:
        item.sku = ''

    try:
        description = driver.find_element(By.XPATH, desc_xpath)
        item.description = description.text.strip()
    except:
        item.description = ''

    img_responce = try_request(img_url)
    img_path = img_url.split('/')[-1]
    img_path = save_pth / img_path

    with open(img_path, 'wb') as file:
        file.write(img_responce.content)

    item.img_rel_path = str(img_path.relative_to(Path(__file__).parent))
    
    return item



class LamodaParser(ChromeParser):
    def __init__(self, *args, **kwargs) -> None:
        chrome_options =(
            '--disable-infobars',
            #'--headless',
            '--ignore-certificate-errors',
            '--no-first-run',
            '--log-level=3',
            '--ignore-certificate-errors-spki-list',
            '--ignore-ssl-errors',
            '--log-level=3',
            '--window-size=1920,1080',
            '--disable-blink-features=AutomationControlled'
        )
        super().__init__(*chrome_options)

        exact_dir = output_dir / f'output_{int(time() * 1000)}'
        if 'begin_dir' in kwargs and kwargs['begin_dir'] is not None:
            sql_s = Path(kwargs['begin_dir'])
            if sql_s.is_dir() and sql_s.exists():
                exact_dir = sql_s
        self.__exact_dir = check_folder_create(exact_dir)
        sql_uri = f"sqlite:///{str(self.__exact_dir)}/db.sqlite3"
        
        self.__engine = create_engine(sql_uri)
        
        
        self.__started = 0.0
        self.__finished = 0.0
        self.__run = False
        self.__delay_s = kwargs['mdelay']
        self.__begin_cat = kwargs['begin'] if 'begin' in kwargs else None
        Base.metadata.create_all(self.__engine)
        self.__Session = Session(self.__engine)



    def __process_items(self, loc: dict, dir: Path, driver: webdriver.Chrome):
        cnt = 0
        url_togo = loc['url']
        forward = None
        run = 0
        while forward or run == 0:
            try_webdriver_get(url_togo, driver)
            cards = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.XPATH, card_link)))
            try:
                forward = WebDriverWait(
                    driver, 
                    10, 
                    ignored_exceptions=(NoSuchElementException, TimeoutException)
                    ).until(EC.presence_of_element_located((By.XPATH, forward_xpath)))
            except TimeoutException:
                forward = None

            if forward:
                url_togo = forward.get_attribute('href')
            hrefs = [a.get_attribute('href') for a in cards]
            for href in hrefs:
                item = get_card_data(href, dir, driver)
                if item is not None:
                    self.__Session.add(item)
                    self.__Session.commit()
                    cnt += 1
                    sys.stdout.write('\033[2K\033[1G')
                    print(f'{str(dir.relative_to(self.__exact_dir)).replace(os.sep, '/')} Скачано: {cnt}', end='', flush=True)
                else:
                    # TODO: Логгирование
                    print(f'Внимание! Не удалось получить данные карточки товара: {href}')

            run += 1

        if cnt < loc['count']:
            # TODO: Логгирование
            print(f'Внимание! Из {loc['count']} скачано {cnt}', end='\r', flush=True)



    def __rget_data(self, links: dict, dir: Path, driver: webdriver.Chrome, begin: str|None = None):
        sleep(2)
        for link in links:
            current_dir = check_folder_create(dir / link)
            #print(f'Переходим {links[link]}')
            try_webdriver_get(links[link], driver)
            promo = driver.find_elements(By.XPATH, promo2_close)
            if len(promo) > 0:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, promo2_close))).click()
            parent_li = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'router-link-exact-active')]/ancestor::li[1]")))
            inner_ul = parent_li.find_elements(By.XPATH, ".//ul[not (contains(@style, 'display: none'))]")
            if len(inner_ul) == 0:
                if begin is not None:
                    if not self.__run and str(current_dir.relative_to(self.__exact_dir)).replace(os.sep, '/') == begin:
                        self.__run = True
                    if not self.__run:
                        continue
                location_dict = {}
                location_dict['name'] = link
                location_dict['url'] = links[link]
                location_dict['count'] = parent_li.find_element(By.XPATH, ".//span[contains(@class, '_found_')]")
                location_dict['count'] = int(location_dict['count'].text.strip())
                self.__process_items(location_dict, current_dir, driver)
                print()
                continue
            
            inner_links = inner_ul[0].find_elements(By.XPATH, ".//a[@role='link']")
            inner_links = links_to_dict(inner_links)
            self.__rget_data(inner_links, current_dir, driver, begin)



    def start(self, *args, **kwargs) -> None:
        self.__started = time()
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        try_webdriver_get(lamoda_url_w, self._driver)
        ul = WebDriverWait(self._driver, 60
                          ).until(EC.presence_of_element_located((By.XPATH, "//ul[@data-v-eff6c8d8='' and descendant::a[@role='link']]")))
        base_links = ul.find_elements(By.XPATH, ".//a[@role='link']")
        base_links = links_to_dict(base_links)
        self.__rget_data(base_links, self.__exact_dir, self._driver, self.__begin_cat)
        self.__finished = time()
        print('Finished!')
