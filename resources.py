"""
Here I keep a bunch of shared functions
"""


@click.command()
@click.option('--update', is_flag=True, prompt=f'{(len(SCRAPER_INSTANCE.terms - SCRAPER_INSTANCE.done))} are not yet collected. \
Do you want to manually add more press y Else Enter\n.')
def update_search_terms(update):
    """
    Update search terms?
    """
    if update:
        print('''You should now input searchterms. Copy in a newline separated list of terms here: \
The added terms to the search_terms file''')
        new_terms = set(input('Input search terms here:\n').split('\n'))
        SCRAPER_INSTANCE.terms.update(new_terms)


def clear_network_monitor(driver):
    """Clear network monitor by refreshing"""
    old_window = driver.current_window_handle
    driver.switch_to.window(WINDOWS['network_monitor'])
    driver.refresh()
    driver.switch_to.window(old_window)


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
    driver.switch_to.window(WINDOWS['recruiter'])
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


def page_link(driver):
    driver.switch_to.window(WINDOWS['recruiter'])
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
