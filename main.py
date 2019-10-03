'''
The program searches linkedin for search terms
defined in an external newline-separeted textfile
(script_requisites/search_terms) or through user_input.

This file just contains the script to run.
'''

import codecs
import html
import json
import time
import os
import re
import pandas as pd
import tqdm
from selenium.webdriver import Chrome
import click
from pick import pick


def load_dataframe(filename):
    "script loads dataframe accross operating systems where encodings might have been changed"
    for encoding in ['utf-8', 'latin-1']:
        try:
            dataframe = pd.read_csv(filename, encoding=encoding)
            return dataframe
        except BaseException:
            pass
    return pd.DataFrame({'success': [], 'term': [], 't': [], 'delta_t': []})


def network_monitor_on(driver):
    global WINDOWS
    driver.execute_script('''window.open("");''')
    # open window and hit the chrome://net-internals/#events
    new_window = driver.window_handles[-1]
    WINDOWS['network_monitor'] = new_window
    # turn full logging on
    full_log_on(driver)


def full_log_on(driver):
    old_window = driver.current_window_handle
    driver.switch_to.window(WINDOWS['network_monitor'])
    # navigate to capture and turn on full log
    driver.get('chrome://net-internals/#capture')
    time.sleep(4)
    for i in range(5):
        success = capture_bytes(driver)
        if success:
            break


def capture_bytes(driver):
    for el in driver.find_elements_by_tag_name('input'):
        if el.get_attribute('id') == 'capture-view-byte-logging-checkbox':
            el.click()
            return True
    else:
        return False

    # navigate to # events igen.
    driver.get('chrome://net-internals/#events')
    # navigate back
    driver.switch_to.window(old_window)


if not os.path.isdir('script_requisites'):
    os.mkdir('script_requisites')
if not os.path.isdir('parsed_data'):
    os.mkdir('parsed_data')
if not os.path.isdir('logs'):
    os.mkdir('logs')

DONE_DF = load_dataframe('logs/done_search.csv')
CHROME_PATH = "/usr/bin/chromedriver"
TITLE = "Do you want to collect extended profile info \
(a lot slower, and at higher risk of getting caught)?"
OPTIONS = ["Collect all, Double profile collections, \
full backend and the MUNK parse (Slowests)",
           "Collect User Profiles using Prof. MUNK's Parse.",
           "Collect only Profile intro from the Search (Fastests)"]
SCRAPER_INSTANCE = LinkedInScraper(CHROME_PATH, DONE_DF, OPTIONS, TITLE)

SCRAPER_INSTANCE.driver.get("https://www.linkedin.com/")
input('Please log in manually, then press Enter when login is done.')
print(f'{len(SCRAPER_INSTANCE.terms)} unique terms in the search_term file.')

with codecs.open('script_requisites/search_terms', 'w', 'utf-8') as f:
    f.write('\n'.join(SCRAPER_INSTANCE.terms))
    f.close()

# ask if searches should be done again, setting 'done' to empty,
# effectively allowing all queries to be rerun.
if click.confirm(
    f'{(len(SCRAPER_INSTANCE.done - set(SCRAPER_INSTANCE.terms)))} \
terms are already collected. Do you want to run it again for updated data? press y, \
else press Enter.'):
    SCRAPER_INSTANCE.done = set()
SCRAPER_INSTANCE.terms = set(
    SCRAPER_INSTANCE.done - set(SCRAPER_INSTANCE.terms))


if SCRAPER_INSTANCE.network:
    network_monitor_on(SCRAPER_INSTANCE.driver)

# open window for searching profiles
SCRAPER_INSTANCE.open_profile_window(driver)

# Login to Recruiter Page
for el in SCRAPER_INSTANCE.driver.find_elements_by_tag_name('a'):
    if el.text == 'Recruiter':
        print('Found recruiter page')
        el.click()
        SCRAPER_INSTANCE.found = True
        break
if not SCRAPER_INSTANCE.found:
    input('Please press the recruiter button, and then press Enter')
time.sleep(2)

SCRAPER_INSTANCE.windows['recruiter'] = SCRAPER_INSTANCE.driver.window_handles[-1]
SCRAPER_INSTANCE.driver.switch_to.window(SCRAPER_INSTANCE.windows['recruiter'])

###### Get data from the search terms ####
# User chooses for standard search within denmark or user defined.
if not os.path.isfile('logs/profile_log.csv'):
    LOGF = open('logs/profile_log.csv', 'w')
    HEADER = ['uid', 't', 'delta_t', 'length', 'extended']
    LOGF.write(','.join(HEADER))
else:
    LOGF = open('logs/profile_log.csv', 'a')

SCRAPER_INSTANCE.collect_data()

print("Success. Scraping finished.")
