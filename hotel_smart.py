import datetime
import os
import time
import yaml
import shutil
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import subprocess



def post_webhook(config, content):
    requests.post(config['webhook']['url'], json={
        'text': content
    })

def make_date_text(text):
    date_list = str(text).split("-")
    year = int(date_list[0])
    month = int(date_list[1])
    day = int(date_list[2])
    return (str(year) + "/" + str(month).zfill(2) + "/" + str(day).zfill(2))

def make_date_text2(text):
    date_list = str(text).split("-")
    year = int(date_list[0])
    month = int(date_list[1])
    day = int(date_list[2])
    return (str(year) + str(month).zfill(2) + str(day).zfill(2))

def make_move_path(type, period):

    return(move_path)

base_path = os.path.dirname(__file__)
config_path = os.path.join(base_path, 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as fp:
    config = yaml.safe_load(fp)
driver_path = config['path']['driver_path']

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(service=ChromeService(driver_path))
driver.maximize_window()

if config['get_data']['manual_date']:
    history_start_date_text = config['get_data']['manual_history_start_date']
    history_end_date_text = config['get_data']['manual_history_end_date']
    onhand_start_date_text = config['get_data']['manual_onhand_start_date']
    onhand_end_date_text = config['get_data']['manual_onhand_end_date']

else:
    history_start_date = datetime.date.today() + datetime.timedelta(days=-7)
    history_end_date = datetime.date.today() + datetime.timedelta(days=-1)
    onhand_start_date = datetime.date.today() + datetime.timedelta(days=0)
    onhand_end_date = datetime.date.today() + datetime.timedelta(days=90)
    history_start_date_text = make_date_text(history_start_date)
    history_end_date_text = make_date_text(history_end_date)
    onhand_start_date_text = make_date_text(onhand_start_date)
    onhand_end_date_text = make_date_text(onhand_end_date)

history_start_year = history_start_date_text.split("/")[0]
history_start_month = history_start_date_text.split("/")[1]
history_start_day = history_start_date_text.split("/")[2]
history_end_year = history_end_date_text.split("/")[0]
history_end_month = history_end_date_text.split("/")[1]
history_end_day = history_end_date_text.split("/")[2]
onhand_start_year = onhand_start_date_text.split("/")[0]
onhand_start_month = onhand_start_date_text.split("/")[1]
onhand_start_day = onhand_start_date_text.split("/")[2]
onhand_end_year = onhand_end_date_text.split("/")[0]
onhand_end_month = onhand_end_date_text.split("/")[1]
onhand_end_day = onhand_end_date_text.split("/")[2]

if config['get_data']['selenium']:
    print('--------ホテルスマートデータ取得開始---------')
    file_list = []
    driver.get(config['hotel_smart']['url'])

    time.sleep(10)

    form_input = driver.find_elements(by=By.CLASS_NAME, value="p-login_input")
    form_input[0].send_keys(config['hotel_smart']['id'])
    form_input[1].send_keys(config['hotel_smart']['pw'])

    login_button = driver.find_elements(by=By.CLASS_NAME, value="c-button")
    login_button[0].click()

    time.sleep(10)

    driver.get(config['hotel_smart']['url'])

    time.sleep(10)

    # "キャンセルを含める"チェックボックスを押下
    checkbox = driver.find_elements(by=By.CSS_SELECTOR, value=".c-checkbox")
    checkbox[1].click()
    checkbox[3].click()

    time.sleep(10)

    if config['get_data']['history']:
        # プルダウン1を選択
        facility_inputs = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")
        all_facility_inputs = [
            elem for elem in facility_inputs
            if elem.is_displayed() and elem.get_attribute("value") == "(全物件)"
        ]
        facility_select = all_facility_inputs[0]
        facility_select.click()
        time.sleep(2)

        # プルダウン1から施設選択
        facility_keyword = "紅葉"
        options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
        matched_options = [
            option for option in options
            if option.is_displayed() and facility_keyword in option.text.strip()
        ]
        matched_options[0].click()
        time.sleep(2)

        # プルダウン2を選択
        property_inputs = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")
        property_select_inputs = [
            elem for elem in property_inputs
            if elem.is_displayed() and elem.get_attribute("value") == "(物件を選択してください)"
        ]
        property_select = property_select_inputs[0]
        property_select_parent = property_select.find_element(
            By.XPATH,
            "./ancestor::div[contains(@class, 'el-input')][1]"
        )
        property_select_parent.click()
        time.sleep(2)

        # プルダウン2から施設選択
        options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
        matched_options = [
            option for option in options
            if option.is_displayed() and facility_keyword in option.text.strip()
        ]
        matched_options[0].click()
        time.sleep(2)

        # エクスポートまで
        input_start_date = driver.find_elements(by=By.CLASS_NAME, value="el-range-input")
        input_start_date[0].click()
        time.sleep(5)
        input_start_date[0].send_keys(history_start_date_text + Keys.TAB + history_end_date_text + Keys.ENTER)
        time.sleep(5)
        export_button = driver.find_elements(by=By.CLASS_NAME, value="c-button_ordinary")
        export_button[0].click()
        time.sleep(30)

        input_start_date[2].click()
        time.sleep(5)
        input_start_date[2].send_keys(history_start_date_text + Keys.TAB + history_end_date_text + Keys.ENTER)
        time.sleep(5)
        export_button[1].click()
        time.sleep(30)

        reservations_history_file_name = f"予約売上_予約単位_ヴィラ紅葉_{history_start_year}年{history_start_month}月{history_start_day}日-{history_end_year}年{history_end_month}月{history_end_day}日_(税抜)"
        rooms_history_file_name = f"予約売上_部屋単位_ヴィラ紅葉_{history_start_year}年{history_start_month}月{history_start_day}日-{history_end_year}年{history_end_month}月{history_end_day}日_(税抜)"
        file_list.extend([dict(type='reservations', period='history', name=reservations_history_file_name), dict(type='rooms', period='history', name=rooms_history_file_name)])

    if config['get_data']['onhand']:
        input_start_date = driver.find_elements(by=By.CLASS_NAME, value="el-range-input")
        input_start_date[0].click()
        time.sleep(5)
        input_start_date[0].send_keys(onhand_start_date_text + Keys.TAB + onhand_end_date_text + Keys.ENTER)
        time.sleep(5)
        export_button = driver.find_elements(by=By.CLASS_NAME, value="c-button_ordinary")
        export_button[0].click()
        time.sleep(30)

        input_start_date[2].click()
        time.sleep(5)
        input_start_date[2].send_keys(onhand_start_date_text + Keys.TAB + onhand_end_date_text + Keys.ENTER)
        time.sleep(5)
        export_button[1].click()
        time.sleep(30)

        reservations_onhand_file_name = f"予約売上_予約単位_ヴィラ紅葉_{onhand_start_year}年{onhand_start_month}月{onhand_start_day}日-{onhand_end_year}年{onhand_end_month}月{onhand_end_day}日_(税抜)"
        rooms_onhand_file_name = f"予約売上_部屋単位_ヴィラ紅葉_{onhand_start_year}年{onhand_start_month}月{onhand_start_day}日-{onhand_end_year}年{onhand_end_month}月{onhand_end_day}日_(税抜)"
        file_list.extend([dict(type='reservations', period='onhand', name=reservations_onhand_file_name), dict(type='rooms', period='onhand', name=rooms_onhand_file_name)])

    driver.close()

    for i in file_list:
        move_path = os.path.join(config['path']['move_path'], config['facility'] + '_' + i['type'] + '_' + i['period'] + '_' + make_date_text2(datetime.date.today()) + '.csv')
        download_path = os.path.join(config['path']['download_path'],i['name'] + '.csv')
        print(f"ダウンロードパス: {download_path}")
        new_path = shutil.move(download_path, move_path)

    print('--------csvダウンロード完了--------')

if config['get_data']['upload']:
    subprocess.run(config['path']['exe_path'])

