"""Main script file."""


import codecs
import html
import json
import sys
import time
import os
import random
import re
from collections import Counter
from urllib.request import urlopen
import pandas as pd
import requests
import tqdm
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from io import BytesIO
from zipfile import ZipFile
from packaging import version


def get_mask(mask_tokens):
    """doc"""
    global token_num
    token = mask_tokens[token_num]
    if len(set(token)) < 8:
        token_num += 1
        token = get_mask(mask_tokens)
    token_num += 1
    return token


def mask_login(user, password):
    """doc"""
    global token_num
    # mash login details with poetry
    urls = [
        'http://shakespeare.mit.edu/hamlet/hamlet.1.1.html',
        'https://ocw.mit.edu/ans7870/6/6.006/s08/lecturenotes/files/t8.shakespeare.txt']
    for url in urls:
        try:
            text = requests.get(url).text
            with codecs.open('script_requisites/mask_poetry', 'w', 'utf-8') as f:
                f.write(text)
            break
        except BaseException:
            pass
    mask_tokens = text.split()
    token_num = 0
    with codecs.open('script_requisites/a_u_t_h_details', 'w', 'utf-8') as f:
        for char in user:
            mask_token = list(get_mask(mask_tokens) + char)
            random.shuffle(mask_token)
            f.write(''.join(mask_token) + ' ')
        f.write('\n\r')
        for char in password:
            mask_token = list(get_mask(mask_tokens) + char)
            random.shuffle(mask_token)
            f.write(''.join(mask_token) + ' ')


def load_details():
    """doc"""
    global token_num
    mask = codecs.open('script_requisites/mask_poetry', 'r', 'utf-8').read()
    mask_tokens = mask.split()
    f = codecs.open('script_requisites/a_u_t_h_details', 'r', 'utf-8')
    user, password = f.read().split('\n\r')
    token_num = 0
    real_u, real_p = '', ''
    for w in user.split():
        mask_token = get_mask(mask_tokens)
        c = Counter(w)
        for char in mask_token:
            c[char] -= 1
        real_u += c.most_common(1)[0][0]
    for w in password.split():
        mask_token = get_mask(mask_tokens)
        c = Counter(w)
        for char in mask_token:
            c[char] -= 1
        real_p += c.most_common(1)[0][0]
    return real_u, real_p


def password_prompt():
    """Get login details"""
    print('Input your login details:\n')
    user = input('username: \t')
    password = input('password: \t')
    ia = input('Are the details correct press Enter, else press n')
    if ia == 'n':
        password_prompt()
    return user, password


def get_auth_details():
    """This function will load login details if present or prompt user for them."""
    # check if auth file exists
    if os.path.isfile('script_requisites/a_u_t_h_details'):
        # Check if user wants to renew the login details
        ia = input(
            'We already have your login details stored. If you want to renew them press y, else Enter.\n')
        if ia == 'y':
            # Get login details
            user, password = password_prompt()
            # store the details in a masked way for security purposes.
            mask_login(user, password)
            # see if it matches
            u, p = load_details()
            if not (u, p) == (user, password):
                print('hmm mask did not succeed will erase the file')
                os.remove('script_requisites/a_u_t_h_details')
        else:
            user, password = load_details()

    else:
        user, password = password_prompt()
        # store the details in a masked way for security purposes.
        mask_login(user, password)
        u, p = load_details()
        if not (u, p) == (user, password):
            print('hmm mask did not succeed will erase the file')
            os.remove('script_requisites/a_u_t_h_details')

    return user, password


def get_version(link):
    """
    Import selenium and initialize browser
    Install chrome
    """
    chrome_version = re.findall('(?:\d+\.?)+', link)[0]
    parsed_version = version.parse(chrome_version)
    return str(parsed_version)


def download_latest_chrome():

    # find link to latest version
    response = requests.get('http://chromedriver.chromium.org/downloads')
    html = response.text
    links = re.findall(
        r'https:\/\/chromedriver\.storage\.googleapis\.com\/index\.html\?path=[0-9.]*/',
        html)
    link = max(links, key=get_version)

    chrome_version = get_version(link)

    osname = sys.platform
    if osname not in set(['win32', 'mac64', 'linux64']):
        if osname == 'darwin':
            osname = 'mac64'
        if 'win' in osname:
            osname = 'win32'
        if osname == 'linux':
            osname = 'linux64'

    # create link from version and operating system name
    zip_path = f'https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_{osname}.zip'

    #####
    # This is just a hack to download the corrext driver
    zip_path = 'https://chromedriver.storage.googleapis.com/77.0.3865.40/chromedriver_linux64.zip'
    #####

    # download driver.
    response = urlopen(zip_path)
    # unpack zip and dump chromedriver
    myzipfile = ZipFile(BytesIO(response.read()))
    download_path = 'script_requisites/'
    myzipfile.extractall(path=download_path)


# Inform user on potential problems with Selenium get_version
def check_selenium_version():
    import selenium
    response = requests.get('https://pypi.org/project/selenium/')
    html = response.text
    latest_version = re.findall('selenium ([0-9.]+)', html)[0]
    current_version = selenium.__version__
    if latest_version != current_version:
        print(
            '''You are currently running an outdated version of selenium.\n Latest version being: %s\t Your version: %s
        If you experience problems with Selenium try to update it using pip.''' %
            (latest_version, current_version))
    return latest_version == current_version


def login(driver, u, p):
    input_nodes = driver.find_elements_by_tag_name('input')
    for node in input_nodes:
        class_name = node.get_attribute('class')
        if class_name == 'login-email':
            node.send_keys(u)
        elif 'session_key' in class_name:
            node.send_keys(u)

        if class_name == 'login-password':
            node.send_keys(p)
        elif 'login-password' in class_name:
            node.send_keys(p)
    # locate submit button and click it
    for node in input_nodes:
        class_name = node.get_attribute('class')
        if class_name == 'login submit-button':
            node.click()
            break
    # Check if login is succesfull.
    time.sleep(5)  # wait for the page to load.
    html = driver.page_source
    if 'Forgot password?' in html:
        print('Login was unsuccesful, do it manually or rerun the script and change the login info.')
        # sys.exit()


def load_dataframe(filename):
    "script loads dataframe accross operating systems where encodings might have been changed"
    for encoding in ['utf-8', 'latin-1']:
        try:
            df = pd.read_csv(filename, encoding=encoding)
            return df
        except BaseException:
            pass
    return pd.DataFrame({'success': [], 'term': [], 't': [], 'delta_t': []})


def network_monitor_on(driver):
    global windows
    driver.execute_script('''window.open("");''')
    # open window and hit the chrome://net-internals/#events
    new_window = driver.window_handles[-1]
    windows['network_monitor'] = new_window
    # turn full logging on
    full_log_on(driver)


def capture_bytes(driver):
    for el in driver.find_elements_by_tag_name('input'):
        if el.get_attribute('id') == 'capture-view-byte-logging-checkbox':
            el.click()
            return True
    else:
        return False


def full_log_on(driver):
    old_window = driver.current_window_handle
    driver.switch_to.window(windows['network_monitor'])
    # navigate to capture and turn on full log
    driver.get('chrome://net-internals/#capture')
    time.sleep(4)
    for i in range(5):
        success = capture_bytes(driver)
        if success:
            break

    # navigate to # events igen.
    driver.get('chrome://net-internals/#events')
    # navigate back
    driver.switch_to.window(old_window)


def clear_network_monitor(driver):
    # Clear network monitor
    # by refreshing
    old_window = driver.current_window_handle
    driver.switch_to.window(windows['network_monitor'])
    driver.refresh()
    driver.switch_to.window(old_window)


def open_profile_window(driver):
    global windows

    driver.execute_script('''window.open("");''')

    new_window = driver.window_handles[-1]
    windows['profiles'] = new_window


######## DATA COLLECTION FUNCTIONS #######
# FUnction for normalizing data

def norm(val):
    if type(val) == str:
        return html.unescape(val)
    else:
        return val


def norm_master(obj):
    if type(obj) == dict:
        return norm_d(obj)
    elif type(obj) == list:
        return norm_l(obj)
    else:
        return norm(obj)


def norm_l(l):
    new = []
    for val in l:
        new.append(norm_master(val))
    return new


def norm_d(d):
    new = {}
    for key, val in d.items():
        new[key] = norm_master(val)
    return new

# Extracting json data from hex encoded bytes in the network monitor


def remove_https_transaction(text):
    # Removes invalid bytes from http transaction data.
    temp = []
    is_http_transaction = True
    for batch in text.split('hex_encoded_bytes =')[1:]:
        if not is_http_transaction:
            # add batch to final string.
            temp.append(batch)

        if 'HTTP_TRANSACTION_READ_BODY' in batch:
            is_http_transaction = True
        else:
            is_http_transaction = False
    text = 'hex_encoded_bytes ='.join(temp)
    return text
    #hex_text = ''.join(hex_re.findall(text))


def get_results_json(driver):
    # extracts hex encoded json
    hex_text = get_hex(driver)
    print(len(hex_text))
    # transforms hex encoded json and loads it
    if len(hex_text) == 0:
        print('No hex data... Error not fixed.')
        return {}
    data = hex_load_json(hex_text)
    return data


def get_hex(driver):
    driver.switch_to.window(windows['network_monitor'])
    el = driver.find_element_by_id('events-view-details-log-box')
    text = el.text
    # process text to remove http transactions irrelevant to the json response
    text = remove_https_transaction(text)
    hex_text = ''.join(hex_re.findall(text))
    return hex_text


def HexToByte(hexStr):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    # The list comprehension implementation is fractionally slower in this case
    #
    #    hexStr = ''.join( hexStr.split(" ") )
    #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
    #                                   for i in range(0, len( hexStr ), 2) ] )

    bytes = []

    hexStr = ''.join(hexStr.split(" "))

    for i in range(0, len(hexStr), 2):
        bytes.append(chr(int(hexStr[i:i + 2], 16)))

    return ''.join(bytes)


def get_char_span(e):
    char = re.findall('char ([0-9]+)', str(e))
    if len(char) > 0:
        return int(char[0])
    else:
        return None


def quick_fix_json(string, edit_char):
    return ''.join([string[0:edit_char], string[edit_char + 1:]])


def recursive_quick_fix(string, max_iter=300):
    "Tries to load a json string, and recursively ... or rather iteratively removes invalid characters"

    for i in range(max_iter):
        try:
            d = json.loads(string)

            return d
        except Exception as e:
            w = get_char_span(str(e))
            string = quick_fix_json(string, w)
    return {}


def hex_load_json(hex_text):
    after_hex = HexToByte(hex_text).translate(
        mpa)  # remove invalid characters in json
    after_hex = after_hex.rsplit('}', maxsplit=1)[
        0] + '}'  # locate end of json
    found = False
    for i in range(min([len(after_hex), 50])):
        if after_hex[i] != '{':  # Look for where the json starts
            continue
        else:
            try:
                d = json.loads(after_hex[i:])
                found = True
                break
            except BaseException:
                pass
    if found:
        return norm_master(d)
    else:
        # locate beginning of json.
        s = '{"' + after_hex.split('{"', maxsplit=1)[1]
        return norm_master(recursive_quick_fix(s))
# Master Functions for getting the data #######3
# new function for getting the data using hex encoding


def locate_xhr_response(driver, api_pattern='api/smartsearch'):
    driver.switch_to.window(windows['network_monitor'])
    # click on the xhr request
    found = False
    for i in range(3):  # reliability issues, will try again if no success
        if found:
            break
        for el in driver.find_elements_by_tag_name('tr'):
            text = el.text
            class_ = el.get_attribute('class')
            if 'source-url-request' in class_:
                if api_pattern in text:
                    print('Local api request located..')
                    found = True
                    el.click()
                    break
    return found


def get_results(driver, api_pattern='api/smartsearch'):
    print('Locating the xhr data in the network log')
    # click on smart_search result
    success = locate_xhr_response(driver, api_pattern=api_pattern)
    if not success:
        print('Error locating xhr response.')
        return {}
    time.sleep(3)
    # locates and parses the hex encoded bytes as json.
    data = get_results_json(driver)
    if len(data) == 0:
        print('error with parsing the results. Will try again')
        # will try again
        time.sleep(5)
        response = locate_xhr_response(driver, api_pattern)
        data = get_results_json(driver)
    # switch back
    driver.switch_to.window(windows['recruiter'])
    return data


def clear_log(driver):
    # clear log and re-setup monitoring
    print('Results succesfully located, will now clear log.')
    clear_network_monitor(driver)
    full_log_on(driver)


# 'api/projects/recent?','groups?_=','companies?_=',
# code id inner_html.
# <!-- {'data'.... }-->


#############################
def get_profile_links(driver):
    driver.switch_to.window(windows['recruiter'])
    source = driver.page_source
    links = set()
    for link in source.split('href="')[1:]:
        link = link.split('"')[0]
        if '/recruiter/profile' in link:
            links.add(link)
    return links


def get_uid(link):
    uid = link.split(',')[0].split('/')[-1]
    return uid

#########
########## LEGACY PARSE ###########


def parse_data_anders(driver, user_link):
    # LEGACY FUNCTION

    rand_sleep = random.randint(2, 4)
    time.sleep(rand_sleep)

    # get experience
    xp_list = []
    xp_section = driver.find_elements_by_id('profile-experience')
    if len(xp_section) > 0:
        xp_results = xp_section[0].find_elements_by_class_name('position')
        if len(xp_results) > 0:
            for every in xp_results:
                finder = every.get_attribute('innerHTML')
                ####### THIS SECTION IS SAVED FOR LATER #####
                ## Remember to do the searchterm mathcing afterwards##
                # for replacement in search_terms['cap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                # for replacement in search_terms['nocap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                ####### THIS SECTION IS SAVED FOR LATER #####
                position = finder.split('start=0">')
                if len(position) > 1:
                    position = position[1].split('</a></h4>')
                    position = position[0]
                else:
                    position = ''
                company = finder.split(
                    'class="searchable"><a target="_blank" ')
                company = company[1]
                if company.startswith('href'):
                    company = company.split('>')
                    co_link = company[0].replace('href="', '')
                    company = company[1].split('</a')
                    company = company[0]
                else:
                    company = ''
                    co_link = ''
                if '<p class="description searchable">' in finder:
                    co_description = finder.split(
                        '<p class="description searchable">')
                    co_description = co_description[-1].split('</p>')
                    co_description = co_description[0]
                else:
                    co_description = ''
                if '<span class="location">' in finder:
                    co_location = finder.split('<span class="location">')
                    co_location = co_location[-1].split('</span>')
                    co_location = co_location[0]
                else:
                    co_location = ''
                xp_list.append({'company': company,
                                'co_link': co_link,
                                'co_description': co_description,
                                'co_location': co_location})

    # get education
    edu_list = []
    edu_section = driver.find_elements_by_id('profile-education')
    if len(edu_section) > 0:
        edu_results = edu_section[0].find_elements_by_class_name('position')
        if len(edu_results) > 0:
            for every in edu_results:
                finder = every.get_attribute('innerHTML')

                # for replacement in search_terms['cap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                # for replacement in search_terms['nocap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                school = finder.split('<h4 class="searchable">')
                school = school[1].split('</h4>')
                school = school[0]
                if '<a href="' in school:
                    school = school.split('" target="_blank">')
                    school_link = school[0].replace('<a href="', '')
                    school = school[1].replace('</a>', '')
                else:
                    school_link = ''
                if '<h5 class="searchable">' in finder:
                    degree = finder.split('<h5 class="searchable">')
                    degree = degree[1].split('</h5>')
                    degree = degree[0]
                else:
                    degree = ''
                edu_list.append(
                    {'school': school, 'degree': degree, 'school_link': school_link})

    # get summary
    summary = driver.find_elements_by_id('profile-summary')
    if len(summary) > 0:
        summary = summary[0].get_attribute('innerHTML')
        summary = summary.replace(
            '<div class="module-header"><h2 class="title">Summary</h2></div><div class="module-body searchable">',
            '')
       # for replacement in search_terms['cap']:
       #     replacable = '<span class="keyword">'+replacement+'</span>'
       #     summary = summary.replace(replacable,replacement)
        # for replacement in search_terms['nocap']:
        #    replacable = '<span class="keyword">'+replacement+'</span>'
        #    summary = summary.replace(replacable,replacement)
    else:
        summary = ''
    # get location
    info_section = driver.find_elements_by_class_name('profile-info')
    if len(info_section) > 0:
        location = info_section[0].find_elements_by_class_name('location')
        if len(location) > 0:
            location = location[0].get_attribute('innerHTML')
            # for replacement in search_terms['cap']:
            #    replacable = '<span class="keyword">'+replacement+'</span>'
            #    location = location.replace(replacable,replacement)
            # for replacement in search_terms['nocap']:
            #    replacable = '<span class="keyword">'+replacement+'</span>'
            #    location = location.replace(replacable,replacement)
            location = location.split('start=0">')
            location = location[1].replace('</a>', '')
        else:
            location = ''
    else:
        location = ''

    # get industry
    info_section = driver.find_elements_by_class_name('profile-info')
    if len(info_section) > 0:
        industry = info_section[0].find_elements_by_class_name('industry')
        if len(industry) > 0:
            industry = industry[0].get_attribute('innerHTML')
            # for replacement in search_terms['cap']:
            #    replacable = '<span class="keyword">'+replacement+'</span>'
            #    industry = industry.replace(replacable,replacement)
            # for replacement in search_terms['nocap']:
            #    replacable = '<span class="keyword">'+replacement+'</span>'
            #    industry = industry.replace(replacable,replacement)
            try:
                industry = industry.split('start=0">')
                industry = industry[1].replace('</a>', '')
            except BaseException:
                industry = '--'
        else:
            industry = ''
    else:
        industry = ''

    # get groups
    group_list = []
    group_section = driver.find_elements_by_id('profile-groups')
    if len(group_section) > 0:
        group_results = group_section[0].find_elements_by_class_name(
            'group-name')
        if len(group_results) > 0:
            for every in group_results:
                finder = every.get_attribute('innerHTML')
                # for replacement in search_terms['cap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                # for replacement in search_terms['nocap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                finder = finder.split('" target="_blank">')
                group = finder[-1].replace('</a>', '')
                group_link = finder[0].replace('<a href="', '')
                group_list.append({'group': group, 'group_link': group_link})

    # get follows
    follow_list = []
    follow_section = driver.find_elements_by_id('profile-company-following')
    if len(follow_section) > 0:
        follow_results = follow_section[0].find_elements_by_class_name(
            'company-name')
        if len(follow_results) > 0:
            for every in follow_results:
                finder = every.get_attribute('innerHTML')
                # for replacement in search_terms['cap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                # for replacement in search_terms['nocap']:
                #    replacable = '<span class="keyword">'+replacement+'</span>'
                #    finder = finder.replace(replacable,replacement)
                finder = finder.split('" target="_blank">')
                finder = finder[0].split('" title="')
                follow = finder[1]
                follow_link = finder[0].replace('<a href="', '')
                follow_list.append(
                    {'follow': follow, 'follow_link': follow_link})

    skill_list = []
    skill_section = driver.find_elements_by_id('profile-skills')
    if len(skill_section) > 0:
        skill_results = skill_section[0].find_elements_by_class_name('skill')
        if len(skill_results) > 0:
            for every in skill_results:
                finder = every.get_attribute('innerHTML')
                # for replacement in search_terms['cap']:
            #        replacable = '<span class="keyword">'+replacement+'</span>'
        #            finder = finder.replace(replacable,replacement)
        #        for replacement in search_terms['nocap']:
        #            replacable = '<span class="keyword">'+replacement+'</span>'
    #                finder = finder.replace(replacable,replacement)
                skill_list.append({'skill': finder})

    d = {
        'summary': summary,
        'skills': skill_list,
        'location': location,
        'industry': industry,
        'xp': xp_list,
        'edu': edu_list,
        'groups': group_list,
        'follows': follow_list}
    d['t_collected'] = time.time()
    return d


#### NEW PROFILE PARSE ###
def parse_data_backend(driver, uid):
    print('Now getting backend api data')
    # get basic profile data in the html
    driver.switch_to.window(windows['network_monitor'])
    try:
        d = get_basic_profile_info(driver, uid)
    except BaseException:
        d = {}
    # get extra connections: groups, companies etc.

    for typ in ['api/projects/recent?', 'groups?_=', 'companies?_=']:
        typ_name = typ.split('/')[-1].strip('_?')
        print('backend_api for %s' % typ_name)
        new_d = get_results(driver, api_pattern=typ)
        d[typ_name] = new_d
    return d


def get_basic_profile_info(driver, uid):
    print('Locating the xhr data in the network log')
    # click on smart_search result
    success = locate_xhr_response(
        driver, api_pattern='searchController=smartSearch')
    if not success:
        print('Error locating xhr response.')
        return {}
    time.sleep(3)
    # locates and parses the hex encoded bytes as json.
    try:
        first_response = get_hex(driver)
        d = recursive_quick_fix(HexToByte(first_response).split(
            '<code id="templates')[1].split('<!--')[1].split('--><')[0])
    except BaseException:
        print('error parsing profile info, will try again ')
        d = {}
    if len(data) == 0:
        print('error with parsing the results. Will try again')
        # will try again
        time.sleep(5)
        response = locate_xhr_response(driver, 'searchController=smartSearch')
        try:
            first_response = get_hex(driver)
            d = recursive_quick_fix(HexToByte(first_response).split(
                '<code id="templates')[1].split('<!--')[1].split('--><')[0])
        except BaseException:
            print('error parsing profile info, will log problem')
            with open('logs/profile_errors', 'a') as f:
                f.write(uid + '\n')
            pass
    if len(d) > 0:
        print('success parsing api profile info.')
    return d

######## DATA COLLECTION FUNCTIONS  END #######


# Automated browsing of pages and searching.
# Enter the Recruiter search domain.

def start_recruiter_search(driver):
    success = False
    for button in driver.find_elements_by_tag_name('button'):
        if button.text == 'Start a new search':
            button.click()
            success = True
            break
    return success


def choose_custom_filter(driver, filter_name='denmark_only'):
    if 'Filter is selected' in driver.page_source:
        return
    for el in driver.find_elements_by_tag_name('button'):
        if 'Custom filters' in el.text:
            el.click()

    filter_on = False
    for el in driver.find_elements_by_tag_name('button'):
        try:
            if filter_name == el.text:
                el.click()
                filter_on = True
                break
        except BaseException:
            pass

    if not filter_on:
        # check if filter was already on:
        if not 'Filter is selected' in driver.page_source:
            input(
                'Applying custom filter did not succeed, input it manually, and Press Enter')
        # Should make a warning sound.


def input_searchterm(driver, term, custom_filter='denmark_only'):
    driver.switch_to.window(windows['recruiter'])
    # try to enter the search.
    success = False
    for i in range(5):
        try:
            success = start_recruiter_search(driver)
            break
        except BaseException:
            continue
        if success:
            break
        else:
            time.sleep(2)
    # if not success:
    #    input('Automation of search: %s failed. I need you to do it manually and press Enter when ready.'%term)
    # check if filter was already on:
   # if not 'Filter is selected' in driver.page_source:
    #    choose_custom_filter(driver,custom_filter)
    success = False
    for el in driver.find_elements_by_tag_name('input'):
        try:
            el.clear()
            el.send_keys(term)
            el.submit()
            success = True
            break
        except BaseException:
            continue
    time.sleep(2)
    print('will now apply the following filter: %s' % custom_filter)
    if not 'Filter is selected' in driver.page_source:
        choose_custom_filter(driver, custom_filter)
    if not success:
        input('Automation of search failed. I need you to do it manually and press Enter when ready.')
        return
# for i in range(5):
#    success = start_recruiter_search(driver)
#    if not success:
#        time.sleep(2)
#    else:
#        break
# if not success:
#    input('Press the start a new search button in the Chrome browser and then press Enter in the script')


def page_link(driver):
    driver.switch_to.window(windows['recruiter'])
    success = False
    for el in driver.find_elements_by_class_name('page-link'):
        try:
            title = el.get_attribute('title')
        except BaseException:
            title = ''
        if 'next' in title.lower():
            # print(title)
            for i in range(5):
                try:
                    el.click()
                    success = True
                except BaseException:
                    pass

            if success:
                break
    return success


def search_results(
        driver,
        term,
        custom_filter='denmark_only',
        user_defined=False):
    print('Now collecting searchterm: %s' % term)
    if not user_defined:

        input_searchterm(driver, term, custom_filter)

        #print('will just use current filter')
    else:
        input(
            'Define your own custom search using the following term: %s\n and press Enter when ready.' %
            term)

    time.sleep(2)
    #
    links = get_profile_links(driver)

    # get data
    if network:
        data = [get_results(driver)]
        clear_log(driver)
    else:
        data = []
    for page in range(int(n_search_results / 25)):
        time.sleep(1)
        for _ in range(5):  # another quickfix..
            try:
                success = page_link(driver)

                break
            except BaseException:
                print('paging error, will try again')
                success = False
        if success:
            print('Success paging %d' % page)
            if network:
                data.append(get_results(driver))
                clear_log(driver)
            links.update(get_profile_links(driver))
        else:
            print('Error paging %d' % page)

            # break

    # get data for no cap: ## GIVER DET MENING?
    if term.lower() != term:
        print('Now collecting searchterm(no_caps): %s' % term.lower())
        if not user_defined:
            input_searchterm(driver, term.lower())
        else:
            input(
                'Define your own custom search using the following term: %s\n and press Enter when ready.' %
                term.lower())

        time.sleep(2)
        links.update(get_profile_links(driver))
        # get data
        if network:
            data.append(get_results(driver))
            # clear_log
            clear_log(driver)
        for page in range(int(n_search_results / 25)):
            time.sleep(1)
            for _ in range(5):  # another quickfix..
                try:
                    success = page_link(driver)
                    break
                except BaseException:
                    print('paging error, will try again')
                    success = False

            if success:
                print('Success paging %d' % page)
                if network:
                    data.append(get_results(driver))
                    # clear log
                    clear_log(driver)
                links.update(get_profile_links(driver))
            else:
                print('Error paging %d' % page)
                break

    return data, links


def collect_data(terms):
    for term in terms:
        data, links = search_results(driver, term, custom_filter=custom_filter)
        # dump parsed data
        with codecs.open('parsed_data/%s_%s_%r' % (term, custom_filter, time.time()), 'w', 'utf-8') as f:
            json.dump([data, list(links)], f)
            # get profile links
            # Alternativ crawling strategy er at udnytte recruiter-søgningen og traversere det mere naturligt
            # ved at trykke næste resultat i søgningen.
        if extended_user_profile > 2:
            continue
        print('Now ready to collect %d links' % len(links))
        for link in tqdm.tqdm(list(links)):
            uid = get_uid(link)
            if uid in profiles_collected:
                print('-', end='')
                continue
            driver.switch_to.window(windows['profiles'])

            driver.get('https://www.linkedin.com' + link)
            d = parse_data_anders(driver, link)

            # dump data
            with codecs.open('parsed_data/profile_data_%s_%s_%r' % (uid, custom_filter, time.time()), 'w', 'utf-8') as f:
                json.dump(d, f)

            if extended_user_profile == 1:

                # collect api data
                if network:
                    d = parse_data_backend(driver, uid)
                    with codecs.open('parsed_data/profile_data_api_%s_%s_%r' % (uid, custom_filter, time.time()), 'w', 'utf-8') as f:
                        json.dump(d, f)
            if network:
                clear_log(driver)
            # dump
            # save log
            profiles_collected.add(get_uid(link))
            json.dump(
                list(profiles_collected), open(
                    'logs/profiles_collected', 'w'))
            # write to profile_log


###########STARTBLOCK1#######################
n_search_results = 1000
ia = input(
    'Do you want to change current default value %d for number of search results? press y else Enter' %
    n_search_results)
if ia == 'y':
    n_search_results = int(
        input('Enter number of results pr search term here: '))
######### Prerequisites ########
# The script needs the following
# - username and password, user will be prompted for that.
# - a working selenium and chromedriver setup.
# Prerequistites
######### Prerequisites ########
# The script needs the following
# - username and password, user will be prompted for that.
# - a working selenium and chromedriver setup.
# create directories
if not os.path.isdir('script_requisites'):
    os.mkdir('script_requisites')
if not os.path.isdir('parsed_data'):
    os.mkdir('parsed_data')
#########
###########ENDBLOCK1#######################

###########STARTBLOCK2#######################
u, p = get_auth_details()
###########ENDBLOCK2#######################

###########STARTBLOCK3#######################
chrome_path = "/usr/bin/chromedriver"
###########ENDBLOCK3#######################

###########STARTBLOCK4#######################
selenium_problem = check_selenium_version()
###########ENDBLOCK4#######################

###########STARTBLOCK5#######################
# Initialize browser/webdriver
driver = Chrome(chrome_path)
# make sure selenium is installed and updated.
# Login to linkedin
# Locate username and password input fields and send login info
driver.get("https://www.linkedin.com/")
###########ENDBLOCK5#######################

###########STARTBLOCK6#######################
try:
    login(driver, u, p)
except BaseException:
    print('Login was unsuccesful, do it manually or rerun the script and change the login info.')
    input('Press Enter when login is done.')

###### Data Collection #####
description = '''The program searches linkedin for searchterms defined in an external newline-separeted textfile (script_requisites/search_terms) or through user_input
'''
# load searchterms
search_terms = 'script_requisites/search_terms'
if os.path.isfile(search_terms):
    terms = set([i.strip() for i in codecs.open(
        search_terms, 'r', 'utf-8').read().split('\n')])
    # remove blank searches
    if '' in terms:
        terms.remove('')
else:
    terms = set()
print('%d unique terms in the search_term file.' % len(terms))
# load search term log.
###########ENDBLOCK6######################
#
###########STARTBLOCK7#######################
if not os.path.isdir('logs'):
    os.mkdir('logs')
# header should be ['term','t','delta_t','success']
done_df = load_dataframe('logs/done_search.csv')
done = set(done_df[done_df.success == 1].term)
ia = input(
    '%d are not yet collected. Do you want to manually add more press y Else Enter\n.' %
    (len(
        terms -
        done)))
if ia == 'y':
    print(
        '''You should now input searchterms. Copy in a newline separated list of terms here:
    The added terms to the search_terms file''')
    new_terms = set(input('Input search terms here:\n').split('\n'))
    terms.update(new_terms)

with codecs.open('script_requisites/search_terms', 'w', 'utf-8') as f:
    f.write('\n'.join(terms))
    f.close()
# ask if searches should be done again
ia = input(
    '%d terms are already collected. Do you want to run it again for updated data? press y, else press Enter.' %
    (len(
        done -
        set(terms))))
if ia == 'y':
    # sets done empty effectively allowing all queries to be rerun.
    done = set()
terms = set(terms - done)

# Ready to collect the search terms using both cap and uncapped words
# turn on network monitor
windows = {}
###########ENDBLOCK7#######################

###########STARTBLOCK8#######################
# Setup Network Logging
network = False  # Turn this on if network logging should be included in the data
if network:
    network_monitor_on(driver)
###########ENDBLOCK8#######################

###########STARTBLOCK9#######################
# open window for searching profiles
open_profile_window(driver)

# Login to Recruiter Page
found = False
for el in driver.find_elements_by_tag_name('a'):
    if el.text == 'Recruiter':
        print('Found recruiter page')
        el.click()
        found = True
        break
if not found:
    input('Please press the recruiter button, and then press Enter')
time.sleep(2)

windows['recruiter'] = driver.window_handles[-1]
driver.switch_to.window(windows['recruiter'])
###########ENDBLOCK9#######################

###########STARTBLOCK10#######################
# define regular expression for extracting hex encoded bytes.
hex_re = re.compile(r'(?:[0-9A-F]{2} )+')
###########ENDBLOCK10#######################

###########STARTBLOCK11#######################
mpa = range(32)
###########ENDBLOCK11#######################

###########STARTBLOCK12#######################
if not os.path.isfile('logs/profiles_collected'):
    profiles_collected = set()
else:
    profiles_collected = set(json.load(open('logs/profiles_collected', 'r')))
###### Get data from the search terms ####
# User chooses for standard search within denmark or user defined.
custom_filter = 'denmark_only'
ia = input(
    'Do you want to change the predefined filter %s? press y else Enter.' %
    (custom_filter))
if ia == 'y':
    while True:
        custom_filter = input(
            'Please input the name of a custom filter saved in the recruiter page.')
        ia = input('Is the input correct? press Enter, else press n')
        if ia != 'n':
            break

while True:
    extended_user_profile = input(
        '''Do you want to collect extended profile info (a lot slower, and at higher risk of getting caught)?
    Press (1) for Collecting all, Double profile collections, full backend and the MUNK parse (Slowests)
    Press (2) for Collecting User Profiles using Prof. MUNK's Parse.
    Press (3) for Collecting Only Profile intro from the Search (Fastests)
    ''')
    if extended_user_profile in set(['1', '2', '3']):
        extended_user_profile = int(extended_user_profile)
        break
    else:
        print('Invalid input try again...')

if not os.path.isfile('logs/profile_log.csv'):
    logf = open('logs/profile_log.csv', 'w')
    header = ['uid', 't', 'delta_t', 'length', 'extended']
    logf.write(','.join(header))
else:
    logf = open('logs/profile_log.csv', 'a')
###########ENDBLOCK12#######################
