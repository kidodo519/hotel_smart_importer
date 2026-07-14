import datetime
import os
import time
import yaml
import shutil
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


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


def get_date_config(config):
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

    return {
        'history_start': history_start_date_text,
        'history_end': history_end_date_text,
        'onhand_start': onhand_start_date_text,
        'onhand_end': onhand_end_date_text,
    }


def split_date_text(date_text):
    year, month, day = date_text.split("/")
    return year, month, day


def make_export_file_name(unit_name, facility_name, start_date_text, end_date_text):
    start_year, start_month, start_day = split_date_text(start_date_text)
    end_year, end_month, end_day = split_date_text(end_date_text)
    return f"予約売上_{unit_name}_{facility_name}_{start_year}年{start_month}月{start_day}日-{end_year}年{end_month}月{end_day}日_(税抜)"


def make_output_file_name(facility_id, data_type, period):
    return f"{facility_id}_{data_type}_{period}_{make_date_text2(datetime.date.today())}.csv"


def select_facility(driver, facility_keyword):
    facility_inputs = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")
    all_facility_inputs = [
        elem for elem in facility_inputs
        if elem.is_displayed() and elem.get_attribute("value") == "(全物件)"
    ]
    facility_select = all_facility_inputs[0]
    facility_select.click()
    time.sleep(2)

    options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
    matched_options = [
        option for option in options
        if option.is_displayed() and facility_keyword in option.text.strip()
    ]
    matched_options[0].click()
    time.sleep(2)

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

    options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
    matched_options = [
        option for option in options
        if option.is_displayed() and facility_keyword in option.text.strip()
    ]
    matched_options[0].click()
    time.sleep(2)


def export_sales_csv(driver, start_date_text, end_date_text):
    input_start_date = driver.find_elements(by=By.CLASS_NAME, value="el-range-input")
    input_start_date[0].click()
    time.sleep(5)
    input_start_date[0].send_keys(start_date_text + Keys.TAB + end_date_text + Keys.ENTER)
    time.sleep(5)
    export_button = driver.find_elements(by=By.CLASS_NAME, value="c-button_ordinary")
    export_button[0].click()
    time.sleep(30)

    input_start_date[2].click()
    time.sleep(5)
    input_start_date[2].send_keys(start_date_text + Keys.TAB + end_date_text + Keys.ENTER)
    time.sleep(5)
    export_button[1].click()
    time.sleep(30)


def upload_to_s3(local_path, s3_info):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=s3_info['access_key_id'],
        aws_secret_access_key=s3_info['secret_access_key'],
    )
    s3_key = s3_info['file_name'] + os.path.basename(local_path)
    s3_client.upload_file(local_path, s3_info['bucket_name'], s3_key)
    print(f"S3アップロード完了: s3://{s3_info['bucket_name']}/{s3_key}")


def process_downloaded_files(config, facility_config, file_list):
    keep_local_csv = config['get_data'].get('keep_local_csv', True)
    upload_enabled = config['get_data'].get('upload', False)
    move_path_base = config['path'].get('move_path')

    for file_info in file_list:
        output_file_name = make_output_file_name(
            facility_config['facility'],
            file_info['type'],
            file_info['period'],
        )
        download_path = os.path.join(config['path']['download_path'], file_info['name'] + '.csv')
        print(f"ダウンロードパス: {download_path}")

        if keep_local_csv:
            facility_move_path = os.path.join(move_path_base, facility_config['facility']) if move_path_base else None
            if facility_move_path:
                os.makedirs(facility_move_path, exist_ok=True)
                local_path = os.path.join(facility_move_path, output_file_name)
                shutil.move(download_path, local_path)
            else:
                local_path = os.path.join(config['path']['download_path'], output_file_name)
                os.rename(download_path, local_path)
        else:
            local_path = os.path.join(config['path']['download_path'], output_file_name)
            os.rename(download_path, local_path)

        if upload_enabled:
            upload_to_s3(local_path, facility_config['s3_info'])

        if not keep_local_csv:
            os.remove(local_path)


def run_facility(config, facility_config, driver_path, options, date_config):
    driver = webdriver.Chrome(service=ChromeService(driver_path), options=options)
    driver.maximize_window()
    file_list = []

    try:
        print(f"--------{facility_config['facility']} ホテルスマートデータ取得開始---------")
        driver.get(facility_config['hotel_smart']['url'])

        time.sleep(10)

        form_input = driver.find_elements(by=By.CLASS_NAME, value="p-login_input")
        form_input[0].send_keys(facility_config['hotel_smart']['id'])
        form_input[1].send_keys(facility_config['hotel_smart']['pw'])

        login_button = driver.find_elements(by=By.CLASS_NAME, value="c-button")
        login_button[0].click()

        time.sleep(10)

        driver.get(facility_config['hotel_smart']['url'])

        time.sleep(10)

        checkbox = driver.find_elements(by=By.CSS_SELECTOR, value=".c-checkbox")
        checkbox[1].click()
        checkbox[3].click()

        time.sleep(10)

        if config['get_data']['history'] or config['get_data']['onhand']:
            select_facility(driver, facility_config['facility_keyword'])

        if config['get_data']['history']:
            export_sales_csv(driver, date_config['history_start'], date_config['history_end'])
            reservations_history_file_name = make_export_file_name(
                '予約単位', facility_config['export_facility_name'],
                date_config['history_start'], date_config['history_end'],
            )
            rooms_history_file_name = make_export_file_name(
                '部屋単位', facility_config['export_facility_name'],
                date_config['history_start'], date_config['history_end'],
            )
            file_list.extend([
                dict(type='reservations', period='history', name=reservations_history_file_name),
                dict(type='rooms', period='history', name=rooms_history_file_name),
            ])

        if config['get_data']['onhand']:
            export_sales_csv(driver, date_config['onhand_start'], date_config['onhand_end'])
            reservations_onhand_file_name = make_export_file_name(
                '予約単位', facility_config['export_facility_name'],
                date_config['onhand_start'], date_config['onhand_end'],
            )
            rooms_onhand_file_name = make_export_file_name(
                '部屋単位', facility_config['export_facility_name'],
                date_config['onhand_start'], date_config['onhand_end'],
            )
            file_list.extend([
                dict(type='reservations', period='onhand', name=reservations_onhand_file_name),
                dict(type='rooms', period='onhand', name=rooms_onhand_file_name),
            ])
    finally:
        driver.close()

    process_downloaded_files(config, facility_config, file_list)
    print(f"--------{facility_config['facility']} csv処理完了--------")


def main():
    base_path = os.path.dirname(__file__)
    config_path = os.path.join(base_path, 'config.yaml')
    with open(config_path, 'r', encoding='utf-8-sig') as fp:
        config = yaml.safe_load(fp)

    if not config['get_data']['selenium']:
        return

    driver_path = config['path']['driver_path']

    options = Options()
    options.add_argument('--headless')
    date_config = get_date_config(config)

    facilities = config.get('facilities') or [config]
    for facility_config in facilities:
        if not facility_config.get('enabled', True):
            print(f"--------{facility_config['facility']} ホテルスマートデータ取得スキップ---------")
            continue

        run_facility(config, facility_config, driver_path, options, date_config)


if __name__ == '__main__':
    main()
