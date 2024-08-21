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
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from lxml import etree


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

def etree_from_driver(driver: webdriver.Chrome):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return etree.HTML(str(soup))

def get_etree_html(url: str, driver: webdriver.Chrome, fail_wait = 5.0, limit = 5):
    try_webdriver_get(url, driver, fail_wait, limit)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return etree.HTML(str(soup))


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
    prod_url = Column(String)
    img_url = Column(String)



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
        self.__img_xpath = "//img[contains(@class, '_image_lpxn') and ancestor::div[@id='reviews-and-questions']]"
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
        '''WebDriverWait(
            self._driver, 5, ignored_exceptions=[TimeoutException]
            ).until(EC.element_to_be_clickable((By.XPATH, self.__promo1_close))).click()'''
        dom = etree_from_driver(self._driver)
        card_div = dom.xpath("//div[@id='reviews-and-questions']")
        #selenium_to_file(self._driver)
        img = dom.xpath("//img[contains(@class, '_image_1') and ancestor::div[contains(@class, 'ui-product-page-gallery')]]")
        img_url = img[0].attrib['src']
        img_url = 'https:' + img_url

        item = LamodaItem()

        item.prod_url = url
        item.img_url = img_url
        #materials = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-material_filling')]")
        #item.materials = materials[0].text.strip() if len(materials) > 0 else ''
        #size_on_model = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-correspond_to_size')]")
        #item.size_on_model = size_on_model[0].text.strip() if len(size_on_model) > 0 else ''
        #model_params = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-model_parameters')]")
        #item.model_params = model_params[0].text.strip() if len(model_params) > 0 else ''
        #model_heigh = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-model_height_on_photo')]")
        #item.model_heigh = model_heigh[0].text.strip() if len(model_heigh) > 0 else ''
        #length = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-length')]")
        #item.lenght = length[0].text.strip() if len(length) > 0 else ''
        #season = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-season_wear')]")
        #item.season = season[0].text.strip() if len(season) > 0 else ''
        #color = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-color_family')]")
        #item.color = color[0].text.strip() if len(color) > 0 else ''
        #cloth_print = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-print')]")
        #item.print = cloth_print[0].text.strip() if len(cloth_print) > 0 else ''
        #knitwear = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-type_of_knitwear')]")
        #item.knitwear = knitwear[0].text.strip() if len(knitwear) > 0 else ''
        #guarantee = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-guarantee_period')]")
        #item.guarantee = guarantee[0].text.strip() if len(guarantee) > 0 else ''
        #prod_country = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-production_country')]")
        #item.prod_country = prod_country[0].text.strip() if len(prod_country) > 0 else ''
        #clasp = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-clothes_clasp')]")
        #item.clasp = clasp[0].text.strip() if len(clasp) > 0 else ''
        sku = dom.xpath("//span[contains(@class, 'ui-product-description-attribute-sku')]")
        try:
            item.sku = sku[0].text.strip()
        except Exception:
            item.sku = ''
  
        try:
            description = card_div[0].xpath(".//span[ancestor::div[contains(@class, '_description_')]]")
            item.description = description[0].text.strip()
        except:
            item.description = ''

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
            dom = get_etree_html(url, self._driver)
            forward = dom.xpath(self.__forward_xpath)
            card_links = dom.xpath(self.__card_xpath)

            if len(card_links) == 0:
                raise PExeption(f'Ошибка! Не удалось получить список товаров. Структура сайта возможно была изменена.')
            
            for link in card_links:
                sleep(self.__delay_s)
                href = link.attrib['href']
                href = self.__lamoda_url_base + href
                item = self.__get_card_data(href, node.dir)
                self.__img_dowloaded += 1
                print(f'Скачано: {self.__img_dowloaded}', end='\r')
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
