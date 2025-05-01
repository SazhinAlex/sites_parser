import undetected_chromedriver as uc
from time import sleep


pth = 'https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/'


if __name__ == '__main__':
    options = uc.ChromeOptions()
    options.add_argument('--headless')

    # Set up WebDriver

    driver = uc.Chrome()
    driver.get(pth)
    print(driver.title)
    #driver.quit()
    sleep(2000)