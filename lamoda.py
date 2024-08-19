from sites_parser import ChromeParser, try_request, PExeption, output_dir, check_folder_create
from pathlib import Path
from time import time, sleep
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, Session
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


Base = declarative_base()


def selenium_to_file(web_driver, print_info = True):
    filename = f'dump_{int(time() * 1000)}.txt'
    with open(filename, 'w', encoding='utf8') as file:
        file.write(BeautifulSoup(web_driver.page_source, 'html5lib').prettify())
    if print_info:
        print(f'Сохранено: {filename}')



def try_webdriver_get(url: str, driver: webdriver.Chrome, fail_wait = 5.0, limit = 5):
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



class LamodaItem(Base):
    __tablename__ = "LamodaItems"

    id = Column(Integer, primary_key=True)
    img_rel_path = Column(String)
    materials = Column(String)
    size_on_model = Column(String)
    model_params = Column(String)
    model_heigh = Column(String)
    lenght = Column(String)
    season = Column(String)
    color = Column(String)
    print = Column(String)
    knitwear = Column(String)
    guarantee = Column(String)
    prod_country = Column(String)
    clasp = Column(String)
    sku = Column(String)
    description = Column(String)



class LamodaTreeNode():
    def __init__(self, data, url, cnt = 0, dir: Path|None = None) -> None:
        self.data = data
        self.url = url
        self.cnt = cnt
        self.parent = None
        self.children = []
        self.dir = dir

    def add_child(self, node: 'LamodaTreeNode') -> None:
        node.parent = self
        self.children.append(node)

    def get_root(self) -> 'LamodaTreeNode':
        parent = self
        while parent:
            if not parent.parent:
                break
            parent = parent.parent
        
        return parent
    

class LamodaParser(ChromeParser):
    def __init__(self, *args, **kwargs) -> None:
        chrome_options =(
            '--disable-infobars',
            '--headless',
            '--ignore-certificate-errors',
            '--no-first-run',
            '--log-level=3',
            '--ignore-certificate-errors-spki-list',
            '--ignore-ssl-errors',
            '--log-level=3'
        )
        super().__init__(*chrome_options)

        self.__lamoda_url_w = 'https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/'
        self.__lamoda_url_base = 'https://www.lamoda.ru'
        self.__selected = 'x-tree-view-catalog-navigation__category_selected'
        self.__subtree = 'x-tree-view-catalog-navigation__subtree'
        self.__found = 'x-tree-view-catalog-navigation__found'
        self.__forward_xpath = "//div[text()='Дальше']/ancestor::a[contains(@class,'router-link-active')]"
        self.__card_xpath = '//a[contains(@class, "x-product-card__pic-catalog")]'
        self.__promo1_close = "//div[contains(@class, 'icon_cross-thin-white')]"
        self.__img_xpath = ".//img[contains(@class, 'x-product-card__pic-img')]"
        self.__img_big_xpath = ".//img[contains(@class, '_image_lpxn') and ancestor::div[@id='reviews-and-questions']]" 
        self.__delay_s = kwargs['mdelay']
        self.__fail_wait = 60
        self.__img_dowloaded = 0
        self.__bad_img = 0
        self.__started = 0.0
        self.__finished = 0.0
        exact_dir = output_dir / f'output_{int(time() * 1000)}'
        self.__root = LamodaTreeNode('Женская одежда', self.__lamoda_url_w, dir=check_folder_create(exact_dir))
        responce = try_request(self.__lamoda_url_w)

        soup = BeautifulSoup(responce.text, 'html5lib')
        base_links = soup.find('ul', 'x-tree-view-catalog-navigation__subtree')
        base_links = base_links.find_all('a', 'x-link')
        
        self.__fill_tree(base_links, self.__root)

        self.__engine = create_engine(f"sqlite:///{str(self.__root.dir)}/db.sqlite3")
        Base.metadata.create_all(self.__engine)
        self.__Session = Session(self.__engine)


    def __get_card_data(self, url: str, save_pth: Path) -> LamodaItem:
        
        try_webdriver_get(url, self._driver)
        WebDriverWait(self._driver, 10).until(EC.element_to_be_clickable((By.XPATH, self.__promo1_close))).click()
        img = self._driver.find_element(By.XPATH, self.__img_big_xpath)
        img_url = img.get_dom_attribute('src')
        img_url = 'https:' + img_url

        item = LamodaItem()
        try:
            item.materials = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-material_filling')]"
                ).text
        except NoSuchElementException:
            item.materials = ''

        try:
            item.size_on_model = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-correspond_to_size')]"
                ).text
        except NoSuchElementException:
            item.size_on_model = ''

        try:
            item.model_params = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-model_parameters')]"
                ).text
        except NoSuchElementException:
            item.model_params = ''

        try:            
            item.model_heigh = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-model_height_on_photo')]"
                ).text
        except NoSuchElementException:
            item.model_heigh = ''

        try:
            item.lenght = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-length')]"
                ).text
        except NoSuchElementException:
            item.lenght = ''

        try:
            item.season = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-season_wear')]"
                ).text
        except NoSuchElementException:
            item.season = ''

        try:
            item.color = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-color_family')]"
                ).text
        except NoSuchElementException:
            item.color = ''

        try:
            item.print = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-print')]"
                ).text
        except NoSuchElementException:
            item.print = ''

        try:
            item.knitwear = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-type_of_knitwear')]"
                ).text
        except NoSuchElementException:
            item.knitwear = ''

        try:
            item.guarantee = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-guarantee_period')]"
                ).text
        except NoSuchElementException:
            item.guarantee = ''

        try:
            item.prod_country = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-production_country')]"
                ).text
        except NoSuchElementException:
            item.prod_country = ''

        try:
            item.clasp = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-clothes_clasp')]"
                ).text
        except NoSuchElementException:
            item.clasp = ''

        try:
            item.sku = self._driver.find_element(
                By.XPATH, "//span[contains(@class, 'ui-product-description-attribute-sku')]"
                ).text
        except NoSuchElementException:
            item.sku = ''

        try:
            desc_div = card_div.find_element(By.XPATH, ".//span[ancestor::div[contains(@class, '_description_')]]")
        except NoSuchElementException:
            item.description = ''

        desc_text = desc_div.text.strip()
        if desc_text != '':
            item.description = desc_text
            
        img_responce = try_request(img_url)
        img_path = img_url.split('/')[-1]
        img_path = save_pth / img_path

        with open(img_path, 'wb') as file:
            file.write(img_responce.content)

        item.img_rel_path = img_path.relative_to(Path(__file__).parent)
        
        return item

    def __fill_tree(self, links: list[BeautifulSoup], tree: LamodaTreeNode) -> dict:
        for link in links:
            sleep(self.__delay_s)
            url = self.__lamoda_url_base + link.get('href')
            responce = try_request(url)
            soup = BeautifulSoup(responce.text, 'html5lib')
            up_li = None
            div_selected = soup.find('div', self.__selected)
            parents = [i for i in div_selected.parents]
            for ptag in parents:
                if not up_li and ptag.name == 'li':
                    up_li = ptag
            
            tree_node = LamodaTreeNode(link.text.strip(), url)
            tree.add_child(tree_node)

            inner_ul = up_li.find('ul', self.__subtree)
            if inner_ul:
                sublist = inner_ul.findChildren('a', 'x-link')
                self.__fill_tree(sublist, tree_node)
            else:
                tree_node.cnt = int(div_selected.findChild('span', self.__found).text)


    def __download_images(self, node: LamodaTreeNode):
        run = 0
        forward = []
        url = node.url
        while len(forward) > 0 or run == 0:
            try_webdriver_get(url, self._driver)
            forward = self._driver.find_elements(By.XPATH, self.__forward_xpath)
            card_links = self._driver.find_elements(By.XPATH, self.__card_xpath)

            if len(card_links) == 0:
                raise PExeption(f'Ошибка! Не удалось получить список товаров. Структура сайта возможно была изменена.')
            
            for link in card_links:
                sleep(self.__delay_s)
                href = link.get_dom_attribute('href')
                href = self.__lamoda_url_base + href
                item = self.__get_card_data(href, node.dir)
                self.__Session.add(item)

            run += 1

            if len(forward) > 0:
                forward_link = forward[0]
                forward_link = forward_link.find_element(By.XPATH, "//a[contains(@class,'router-link-active')]")
                forward_link = forward_link.get_dom_attribute('href')
                url = self.__lamoda_url_base + forward_link


    def __rget_data(self, node: "LamodaTreeNode"):
  
        if node.dir is None:
            node.dir = output_dir / node.data if node.parent is None else node.parent.dir / node.data
            if not node.dir.exists() or not node.dir.is_dir():
                node.dir.mkdir()

        if node.cnt > 0:
            self.__download_images(node)

        for child in node.children:
            self.__rget_data(child)


    def start(self, *args, **kwargs) -> None:
        self.__started = time()
        
        self.__rget_data(self.__root.get_root())
        self.__finished = time()
        print('Finished!')
