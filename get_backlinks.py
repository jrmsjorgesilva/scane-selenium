#!/usr/bin/env python

import codecs
import os
from time import sleep

from merge_files import concatenate_and_clean

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Constants
URL_BASE = u'https://ahrefs.com/site-explorer/backlinks/v5/external/prefix/live/all/dofollow/1/ahrefs_rank_desc?target='
EMAIL = 'allegade.virtualestates@gmail.com'
PASSWORD = 'Webs!te1'

# File paths
pwd = os.getcwd()
INPUT_FILES_PATH = '{}/put_files_here'.format(pwd)
DOWNLOADS_PATH = '{}/downloads'.format(pwd)
OUTPUT_FILES_PATH = '{}/merged_files'.format(pwd)


def login():
    # There is usually a cookie banner which we need to close to reveal
    # the login button. If its not there just continue
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.iubenda-cs-close-btn')
            )
        ).click()
    except TimeoutException:
        pass

    driver.find_element_by_xpath('//a[contains(@href, "login")]').click()

    el_input_email = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name=email]'))
    )
    el_input_password = driver.find_element_by_css_selector(
        'input[name=password]'
    )
    el_button_submit = driver.find_element_by_css_selector(
        'input[type=submit]'
    )

    actions = ActionChains(driver)
    actions.send_keys_to_element(el_input_email, EMAIL)
    actions.send_keys_to_element(el_input_password, PASSWORD)
    actions.click(el_button_submit)
    actions.perform()


def export_link_data():
    # Click the export button
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, 'export_button'))
    ).click()

    # Wait for modal to open and click `full export`
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, 'start_full_export'))
    ).click()

    # Click the `start export` button
    driver.find_element_by_id('start_export_button').click()


def download_files():
    # Click the __tray__ icon in the menu bar then click all the
    # `a` tags in order to download them
    a_tag_name = 'a[name=link_to_download]'
    el_id = 'top_notifications'

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, el_id))
    )

    driver.execute_script(
        'document.getElementById("{}").click();'.format(el_id)
    )

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, a_tag_name))
    )

    a_tags = driver.find_elements_by_css_selector(a_tag_name)
    for a_tag in a_tags:
        a_tag.click()


def sleep_then_download():
    # Quick hack to remove notification as it was blocking the download button
    driver.refresh()
    # Sleep to make sure all files have completed export
    sleep(300)
    download_files()


def clear_file_dropdown():
    driver.find_element_by_id('removeAllExportedFiles').click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.modal'))
    )
    driver.execute_script("deleteCSVFile('all');")


if __name__ == '__main__':
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_experimental_option(
        'prefs', {'download.default_directory': DOWNLOADS_PATH}
    )
    driver = webdriver.Chrome(chrome_options=chromeOptions)

    input_files = filter(
        lambda f: f[0] is not '.', os.listdir(INPUT_FILES_PATH)
    )
    should_login = True

    # Iterate through each file in the `INPUT_FILES_PATH`
    for i, file in enumerate(input_files):
        print 'Processing file no. {file_num} of {num_files}: {name}'.format(
            file_num=i + 1,
            num_files=len(input_files),
            name=file,
        )

        # Read each file line by line (target url by targe url)
        file_path = '{0}/{1}'.format(INPUT_FILES_PATH, file)
        for encoding in ['utf-16', 'utf-8']:
            try:
                with codecs.open(file_path, encoding=encoding) as f:
                    for j, line in enumerate(f):
                        driver.get(URL_BASE + line.rstrip('\n'))
                        if should_login:
                            login()
                            should_login = False
                        try:
                            export_link_data()
                        except TimeoutException:
                            pass

                        # Export 100 files, download them, clean up, continue
                        if j > 0 and j % 100 == 0:
                            try:
                                sleep_then_download()
                                # Sleep to make sure all files have completed
                                # downloading
                                sleep(300)
                                clear_file_dropdown()
                            except TimeoutException:
                                pass

                    # Download any of the leftovers
                    try:
                        sleep_then_download()
                        sleep(300)
                        clear_file_dropdown()
                    except TimeoutException:
                        pass
            except UnicodeError:
                pass

        concatenate_and_clean(file)

    driver.quit()
