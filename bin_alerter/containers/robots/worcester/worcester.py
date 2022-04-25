import datetime
import time
from os import environ as osenv
import requests
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


ADDRESS : str = osenv.get('ADDRESS')
POSTCODE : str = osenv.get('POSTCODE')
BOT_TOKEN : str = osenv.get('BOT_TOKEN')
CHAT_ID : str = osenv.get('CHAT_ID')

# Build Selenium Driver
def selenium_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = '/opt/chrome/chrome'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x1696')
    options.add_argument('--single-process')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-dev-tools')
    options.add_argument('--no-zygote')
    options.add_argument(f'--user-data-dir={mkdtemp()}')
    options.add_argument(f'--data-path={mkdtemp()}')
    options.add_argument(f'--disk-cache-dir={mkdtemp()}')
    options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome('/opt/chromedriver', options=options)
    return driver

# Scrape council site data
def scrape_council_site():
    driver = selenium_driver()
    driver.get('https://selfserve.worcester.gov.uk/wccroundlookup/HandleSearchScreen')
    
    driver.implicitly_wait(3.2)
    driver.find_element(by=By.ID, value='ccc-recommended-settings').click()
    post_code_search = driver.find_element(by=By.NAME, value='nmalAddrtxt') 
    time.sleep(1.4)
    post_code_search.send_keys(POSTCODE)
    driver.find_element(by=By.NAME, value='nmalAddrbtn').click()
    time.sleep(1.7)
    driver.find_element(by=By.NAME, value='alAddrsel').click()
    address_select = Select(driver.find_element(by=By.NAME, value='alAddrsel'))
    address_select.select_by_visible_text(ADDRESS)
    time.sleep(1.1)
    driver.find_element(by=By.NAME, value='btnSubmit').click()
    driver.implicitly_wait(5)

    collections = []
    result_table = driver.find_element(by=By.CSS_SELECTOR, value='table.table-striped')
    for row in result_table.find_elements(by=By.CSS_SELECTOR, value='tr'):
        collection = row.text.split(' collection')
        collection[1] =  collection[1][-10:]
        collections.append(collection)

    time.sleep(2.3)
    driver.quit()
    return collections


def standard_collection(collections):
    rotation = ['Non-recyclable waste', 'Recycling']
    selected_collections = []
    for collection in collections:
        if collection[0] in rotation:
            collection[1] = collection[1] + ' 07:00:00'
            collection[1] = datetime.datetime.strptime(collection[1], '%d/%m/%Y %H:%M:%S')
            selected_collections.append(collection)
    
    selected_collection = selected_collections[0]
    for collection in selected_collections:
        if collection[1] < selected_collection[1]:
            selected_collection = collection

    if selected_collection[0] == 'Recycling':
        selected_collection.append('GREEN')
    if selected_collection[0] == 'Non-recyclable waste':
        selected_collection.append('BLACK')
    return selected_collection


def garden_waste_collection(collections):
    rotation = ['Garden waste']
    selected_collections = []

    for collection in collections:
        if collection[0] in rotation:
            collection[1] = collection[1] + ' 07:00:00'
            collection[1] = datetime.datetime.strptime(collection[1], '%d/%m/%Y %H:%M:%S')
            selected_collections.append(collection)

    selected_collection = selected_collections[0]
    if selected_collection[0] == 'Garden waste':
        selected_collection.append('BROWN')
        
    return selected_collection

def send_telegram(message):
    url_string = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&parse_mode=Markdown&text={message}'
    response = requests.get(url_string)
    print('SENDTELEGRAM: Message sending')
    print(response.json())


def message_builder(colour, date):
    brown_square = '🟫'
    black_square = '⬛'
    green_square = '🟩'
    trash_can = '🗑️'
    square = locals()[colour.lower() + '_square']
    return f'{trash_can} {square} {colour.upper()} BIN {square} {trash_can} due out for collection tomorrow {date} '


def check_alert_collection(collection):
    TIME_THRESHOLD = 24
    now_time = datetime.datetime.now()
    time_difference = collection[1] - now_time
    time_difference_hours = time_difference.total_seconds()/(60*60)
    print(str(time_difference_hours))
    
    if int(time_difference_hours) < TIME_THRESHOLD:
        bin_colour = collection[2]
        bin_date =  collection[1].strftime('%d/%m/%Y')
        message = message_builder(bin_colour, bin_date)
        send_telegram(message)    
        print(message)


def handler(event, context):
    collections = scrape_council_site()
    collection = standard_collection(collections)
    check_alert_collection(collection)
    
    collection = garden_waste_collection(collections)
    check_alert_collection(collection)

