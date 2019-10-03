"""
Here I store the classes
"""


class LinkedInScraper:
    """
    Main class for scraping LinkedIn
    Ready to collect the search terms using both cap and uncapped words
    turn on network monitor
    """

    def __init__(self, chrome_path, done_df, options, title):
        self.windows = {}
        self.n_search_results = click.prompt(
            "How many results per search do you want?", type=int, default=1000)
        self.driver = Chrome(chrome_path)
        self.terms = set_search_terms()
        self.done = set(done_df[done_df.success == 1].term)
        _, self.extended_user_profile = pick(options, title)
        self.network = False  # Turn this on if network logging should be included in the data
        self.found = False
        self.profiles_collected = collect_profiles()
        self.custom_filter = click.prompt('Please input the name of a custom filter \
    saved in the recruiter page.', type=str, default='denmark_only')

    def search_results(driver, term, custom_filter, user_defined=False):
        print('Now collecting searchterm: %s' % term)
        if not user_defined:
            input_searchterm(driver, term, custom_filter)
        else:
            input(
                'Define your own custom search using the following term: %s\n and press Enter when ready.' %
                term)
        time.sleep(2)
        links = get_profile_links(driver)

        # get data
        if NETWORK:
            data = [get_results(driver)]
            clear_log(driver)
        else:
            data = []
        for page in range(int(N_SEARCH_RESULTS / 25)):
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
                if NETWORK:
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
            if NETWORK:
                data.append(get_results(driver))
                # clear_log
                clear_log(driver)
            for page in range(int(N_SEARCH_RESULTS / 25)):
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
                    if NETWORK:
                        data.append(get_results(driver))
                        # clear log
                        clear_log(driver)
                    links.update(get_profile_links(driver))
                else:
                    print('Error paging %d' % page)
                    break

        return data, links

    def collect_data(self):
        """This function collects data."""
        for term in self.terms:
            data, links = search_results(driver, term, custom_filter)
            # dump parsed data
            with codecs.open(f'parsed_data/{terms}_{custom_filter}_{time.time()}',
                             'w', 'utf-8') as parse_file:
                json.dump([data, list(links)], parse_file)
                """Get profile links.
                        Alternativ crawling strategy er at udnytte recruiter-søgningen
                        og traversere det mere naturligt ved at trykke næste resultat i søgningen."""
            if self.extended_user_profile > 1:
                continue
            print('Now ready to collect %d links' % len(links))
            for link in tqdm.tqdm(list(links)):
                uid = get_uid(link)
                if uid in self.profiles_collected:
                    print('-', end='')
                    continue
                self.driver.switch_to.window(WINDOWS['profiles'])

                self.driver.get('https://www.linkedin.com' + link)
                d = parse_data_anders(self.driver)

                # dump data
                with codecs.open('parsed_data/profile_data_%s_%s_%r' % (uid, custom_filter, time.time()), 'w', 'utf-8') as f:
                    json.dump(d, f)

                if self.extended_user_profile == 0:
                    # collect api data
                    if self.network:
                        d = parse_data_backend(driver, uid)
                        with codecs.open('parsed_data/profile_data_api_{uid}_{self.custom_filter}_{time.time()}') as f:
                            json.dump(d, f)

                if self.network:
                    clear_log(self.driver)
                # dump, save log
                self.profiles_collected.add(get_uid(link))
                json.dump(list(self.profiles_collected),
                          open('logs/profiles_collected', 'w'))

    def open_profile_window(self):
        self.driver.execute_script('''window.open("");''')
        new_window = self.driver.window_handles[-1]
        self.windows['profiles'] = new_window

    def get_uid(link):
        uid = link.split(',')[0].split('/')[-1]
        return uid

    def clear_log(driver):
        """
        Clear log and re-setup monitoring
        """
        print('Results succesfully located, will now clear log.')
        clear_network_monitor(driver)
        full_log_on(driver)

    def set_search_terms():
        """
        Read search terms.
        """
        search_terms = 'script_requisites/search_terms'
        if os.path.isfile(search_terms):
            terms = codecs.open(search_terms, 'r', 'utf-8').read().split('\n')
            terms = {term.strip() for term in terms}
        # remove blank searches
        if '' in terms:
            terms.remove('')
        else:
            terms = set()
        return terms

    def collect_profiles():
        if not os.path.isfile('logs/profiles_collected'):
            return set()
        return set(json.load(open('logs/profiles_collected', 'r')))


class Parser:

    """
    The main data parser contains both the legacy and new parser functions 
    """

    def __init__(self, parse_type):
        self.parse_type = parse_type

    def parse_data_anders(self, driver):
        """Legacy parse function"""

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
            edu_results = edu_section[0].find_elements_by_class_name(
                'position')
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

    def parse_data_backend(self, driver, uid):
        print('Now getting backend api data')
        # get basic profile data in the html
        driver.switch_to.window(WINDOWS['network_monitor'])
        try:
            d = get_basic_profile_info(driver, uid)
        except BaseException:
            d = {}

        for typ in ['api/projects/recent?', 'groups?_=', 'companies?_=']:
            typ_name = typ.split('/')[-1].strip('_?')
            print('backend_api for %s' % typ_name)
            new_d = get_results(driver, api_pattern=typ)
            d[typ_name] = new_d
        return d

    def get_basic_profile_info(self, driver, uid):
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
                    finder = finder.split('" target="_blank">')
                    group = finder[-1].replace('</a>', '')
                    group_link = finder[0].replace('<a href="', '')
                    group_list.append(
                        {'group': group, 'group_link': group_link})

        # get follows
        follow_list = []
        follow_section = driver.find_elements_by_id(
            'profile-company-following')
        if len(follow_section) > 0:
            follow_results = follow_section[0].find_elements_by_class_name(
                'company-name')
            if len(follow_results) > 0:
                for every in follow_results:
                    finder = every.get_attribute('innerHTML')
                    finder = finder.split('" target="_blank">')
                    finder = finder[0].split('" title="')
                    follow = finder[1]
                    follow_link = finder[0].replace('<a href="', '')
                    follow_list.append(
                        {'follow': follow, 'follow_link': follow_link})

        skill_list = []
        skill_section = driver.find_elements_by_id('profile-skills')
        if len(skill_section) > 0:
            skill_results = skill_section[0].find_elements_by_class_name(
                'skill')
            if len(skill_results) > 0:
                for every in skill_results:
                    finder = every.get_attribute('innerHTML')
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


class DataCollector:
    """
    This is for data collection
    """

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
            data = get_results_json(driver)
        # switch back
        driver.switch_to.window(WINDOWS['recruiter'])
        return data

    def locate_xhr_response(driver, api_pattern='api/smartsearch'):
        driver.switch_to.window(WINDOWS['network_monitor'])
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
        # define regular expression for extracting hex encoded bytes.
        hex_re = re.compile(r'(?:[0-9A-F]{2} )+')

        driver.switch_to.window(WINDOWS['network_monitor'])
        el = driver.find_element_by_id('events-view-details-log-box')
        text = el.text
        # process text to remove http transactions irrelevant to the json response
        text = remove_https_transaction(text)
        hex_text = ''.join(hex_re.findall(text))
        return hex_text

    def hex_load_json(hex_text):
        mpa = range(32)
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

    def HexToByte(hexStr):
        """
        Convert a string hex byte values into a byte string. The Hex Byte values may
        or may not be space separated.
        """
        bytes = []
        hexStr = ''.join(hexStr.split(" "))
        for i in range(0, len(hexStr), 2):
            bytes.append(chr(int(hexStr[i:i + 2], 16)))

        return ''.join(bytes)

    def recursive_quick_fix(string, max_iter=300):
        """Tries to load a json string, and recursively...
        or rather iteratively removes invalid characters"""
        for i in range(max_iter):
            try:
                d = json.loads(string)

                return d
            except Exception as e:
                w = get_char_span(str(e))
                string = quick_fix_json(string, w)
        return {}

    def quick_fix_json(string, edit_char):
        return ''.join([string[0:edit_char], string[edit_char + 1:]])

    def get_char_span(e):
        char = re.findall('char ([0-9]+)', str(e))
        if len(char) > 0:
            return int(char[0])
        return None

    def get_profile_links(driver):
        driver.switch_to.window(WINDOWS['recruiter'])
        source = driver.page_source
        links = set()
        for link in source.split('href="')[1:]:
            link = link.split('"')[0]
            if '/recruiter/profile' in link:
                links.add(link)
        return links


class Normalizer:
    """
    This class is used for normalizing data.
    """
    def norm_master(obj):
        if type(obj) == dict:
            return norm_d(obj)
        elif type(obj) == list:
            return norm_l(obj)
        else:
            return norm(obj)

    def norm_d(d):
        new = {}
        for key, val in d.items():
            new[key] = norm_master(val)
        return new

    def norm_l(l):
        new = []
        for val in l:
            new.append(norm_master(val))
        return new

    def norm(val):
        """FUnction for normalizing data"""
        if type(val) == str:
            return html.unescape(val)
        else:
            return val
