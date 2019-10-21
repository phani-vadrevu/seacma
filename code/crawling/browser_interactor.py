#! /usr/bin/python
###########################################################################
# Copyright (C) 2018 Phani Vadrevu                                        #
# phani@cs.uno.edu                                                        #
#                                                                         #
# Distributed under the GNU Public License                                #
# http://www.gnu.org/licenses/gpl.txt                                     #
#                                                                         #
# This program is free software; you can redistribute it and/or modify    #
# it under the terms of the GNU General Public License as published by    #
# the Free Software Foundation; either version 2 of the License, or       #
# (at your option) any later version.                                     #
#                                                                         #
###########################################################################
# TODO-1: Make changes in the browser code so that devtools is activated for each tab automatically
# This makes a lot of things easier: for example, we don't have to reload newly opened tabs to check for
# downloads
# TODO: Test this page: "http://www.phanivadrevu.com/tests/annoying_login.php"
# TODO: Like above, see infinte alert pages act

import time
import subprocess
# import signal
import os
import tldextract
import logging
import timeout_decorator
import shutil
import traceback

import get_clickable_elements
from utils import mark_coordinates, us_timestamp_str
from devtools_client import DevToolsClient
import config
import utils

SHORT_PAUSE = 10
VERY_SHORT_PAUSE = 1
USEFUL_ACTION_REPEAT = 2


class BrowserInteractor(object):
    def __init__(self, log_id, start_url=None, agent_name="edge_win"):
        self.start_time = time.time()
        self.agent_name = agent_name
        self.log_id = log_id
        self.logger = logging.getLogger(log_id)

        self.screenshots_dir_path = os.path.join(config.MAIN_LOG_PATH, config.SCREENSHOTS_DIR, self.log_id)
        os.mkdir(self.screenshots_dir_path)

        self.html_logs_dir_path = os.path.join(config.MAIN_LOG_PATH, config.HTML_LOGS_DIR, self.log_id)
        os.mkdir(self.html_logs_dir_path)

        # Every time the browser is restarted the browser_counter increases
        # this counter is used to name the JSGraph log file uniquely.
        self.browser_counter = 1

        tab = self.open_browser(start_url)
        self.start_url = start_url

        self._save_html(tab)
        
        # Useful when milking
        sshot_path = self._take_screenshot(tab)
        self.logger.info("The screenshot of loaded home page: %s", sshot_path)
        # Sometimes, websites might redirect to a different site. We would like to use the
        # name of this redirected site instead of the original one
        self.url = self.devtools_client.get_tab_url(tab)

        self.tabs_opened = 0
        self.overall_tabs_opened = 0

        self.logger.info("Home URL: %s", self.url)
        # current state.
        self.state = []
        self.restart = False
        # VERY STRANGELY, some ad networks fail to display ads when there is a live TLD lookup from Python code!
        # I have no idea why this request is interfering with that at all.
        # However, we are disabling the live lookup of suffixes. Only the stored list is used.
        self.tld_extract = tldextract.TLDExtract(suffix_list_urls=None)
        self.home_domain = self.tld_extract(self.url).registered_domain



    # TODO: should move this elsewhere as get_clickable_elements also use this code for testing
    def open_browser(self, start_url):
        # TODO: Disable GSB!!
        #binary_location = '/usr/bin/google-chrome-unstable'
        binary_location = os.path.join(config.CHROME_BINARY_PATH, 'chrome')
        args = [binary_location]

        # This flag is needed as Docker has a root user and chrome doesn't support root users
        # unless there's a no-sandbox flag.
        args.append('--no-sandbox')
        args.append('--headless')
        #args.append('--incognito')
        args.append('--disable-popup-blocking')
        # Note: "start-maximized has no effect in headless mode which by default is in 800x600.
        # We need to explicitly set the window size that we would like.
        #options.add_argument('--start-maximized')
        # TODO: Use setDeviceMetricsOverride in https://chromedevtools.github.io/devtools-protocol/tot/Emulation
        # to emulate mobile devices. Even for desktop have setting that give the proper screen size etc.

        args.append('--window-size=%s,%s' % config.USER_AGENTS[self.agent_name]['window_size_cmd'])

        # Note that the logging only works in headless mode. The difference between logging for
        # headless and head is due to a bug in this version of Chromium.
        # This version of Chromium (64.0.3282.204) stores these logs in
        # the CHROME_BINARY_PATH directory; this cannot be changed.
        jsgraph_log_name = "%s_%s.jsgraph.log" % (self.log_id, self.browser_counter)
        self.logger.info('JSGraph log file: %s', jsgraph_log_name)
        args.append('--enable-logging=%s' % (jsgraph_log_name,))
        args.append('--disk-cache-size=1')

        # Note: Don't use extra quotes around user-agent here.this will trip Cloud Fare's Browser Integrity Check
        # Make sure there are no quotes around the UA by checking here:
        # https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending
        args.append('--user-agent=%s' % (config.USER_AGENTS[self.agent_name]['user_agent'],))

        # Creating a new temporary directory - so that it will not have any cache
        chrome_data_path = os.path.join(config.MAIN_LOG_PATH,
                                        config.CHROMEDATA_DIR,
                                        "%s" % (self.log_id,))
        os.mkdir(chrome_data_path)
        args.append('--user-data-dir=%s' % (chrome_data_path,))

        #capabilities = DesiredCapabilities.CHROME
        # This allows driver.get() call to return immediately. If not, it wait until the page loads
        # which can be a problem on certain pages.
        #capabilities['pageLoadStrategy'] = "none"

        port_number = utils.fetch_random_free_port()
        args.append('--remote-debugging-port=%s' % (port_number,))
        #shell_cmd = "%s %s" % (binary_location, args)
        #print "Shell command: %s" % (shell_cmd,)
        print args
        with open(os.devnull, 'w') as DEVNULL:
            process = subprocess.Popen(args, stdout=DEVNULL, stderr=subprocess.STDOUT)
            #process = subprocess.Popen(args, stdout=DEVNULL)

        #print "Browser process ID:", process.pid
        self.browser_pid = process.pid

        # Wait a bit to make sure that the process will start and devtools client can connect
        time.sleep(VERY_SHORT_PAUSE)
        self.devtools_client = DevToolsClient(self.log_id, port_number, self.agent_name, browser_pid=self.browser_pid)
        tab = self.devtools_client.open_fresh_tab(start_url)

        print "Current URL:", self.devtools_client.get_tab_url(tab)
        #print "Time:", (time.time()-self.start_time)
        return tab


    def make_click(self, coords, tab):
        try:
            x, y = coords
            click_result = self.devtools_client.make_click(x, y, tab)
        except Exception as e:
            print "Exception during click: ", e
            traceback.print_exc()
            return None
        return click_result

    # TODO: Move all this error handling code to devtools_client
    # Tries to take screenshot a couple of times before giving up
    def _take_screenshot(self, tab, third_party=False):
        for i in range(2):
            try:
                file_path = self._take_screenshot_unsafe(tab)
            except Exception as e:
                self.logger.info("Exception in _take_screenshot(); timed out probably")
                print "Exception in _take_screenshot(); timed out probably"
                # Sometimes, take_screenshot hangs; in this case, hopefully reloading will solve the issue
                if i == 0:
                    tab.Page.reload()
                    time.sleep(SHORT_PAUSE)
            else:
                # If a screenshot was taken and the page is an ad, also save a dump of the page's source code.
                if third_party:
                    self._save_html(tab)
                return file_path
        self.logger.info("_take_screenshot(): Raising Exception")
        #raise e

    @timeout_decorator.timeout(SHORT_PAUSE)
    def _take_screenshot_unsafe(self, tab):
        k = time.time()
        us_timestamp = us_timestamp_str()
        file_name = "%s.png" % (us_timestamp,)
        file_path = os.path.join(self.screenshots_dir_path,
                                 file_name)
        self.devtools_client.capture_screenshot(tab, file_path)
        print "sshot_time:", (time.time() - k)
        return file_path

    @timeout_decorator.timeout(SHORT_PAUSE)
    def _save_html_unsafe(self, tab):
        us_timestamp = us_timestamp_str()
        file_name = "%s.html" % (us_timestamp,)
        file_path = os.path.join(self.html_logs_dir_path, file_name)
        node_id = tab.DOM.getDocument()['root']['nodeId']
        html = tab.DOM.getOuterHTML(nodeId=node_id)['outerHTML']
        html = html.encode('ascii', 'ignore').decode('ascii')
        with open(file_path, 'wb') as f:
            f.write(html)
        self.logger.info('Saved HTML in file: %s', file_path)

    def _save_html(self, tab):
        try:
            self._save_html_unsafe(tab)
        except Exception as e:
            self.logger.info("Failure in saving HTML!")
            print "Exception in save_html:", e

    def log_downloads(self,):
        downloads = utils.check_for_downloads()
        print "Downloads: %s" % (downloads,)
        for fname, fhash in downloads:
            self.logger.info("Downloaded a file: %s, Hash: %s", fname, fhash)
        return len(downloads) > 0

    def process_3p_page(self, tab):
        url = self.devtools_client.get_tab_url(tab)
        self.logger.info("3rd party page URL: %s", url)
        if url != "about:blank":
            file_path = self._take_screenshot(tab, third_party=True)
            self.logger.info("Screenshot: %s", file_path)
        # If url is "about:blank" then, there could be a download and we should reload
        # to check for it. The download will not appear on first attempt as Devtools Client will be disabled
        # for that page. We will need to reload it with window_open url if that's available.
        elif self.devtools_client.last_window_open_url is not None:
            tab = self.devtools_client.open_fresh_tab(
                                    self.devtools_client.last_window_open_url,
                                    old_tab=tab)
            self.devtools_client.last_window_open_url = None
            self.log_downloads()
        self.devtools_client.close_tab(tab)

    def get_click_coords(self,):
        tab = self.fetch_a_home_tab()
        elem_coords = get_clickable_elements.get_clickable_elements(tab, self.agent_name)
        return elem_coords

    # These vars keep track of the current URL and the tabs that have been opened
    # thus far.
    def reset_per_action_vars(self, tab):
        self.tabs_opened = 0
        self.url = self.devtools_client.get_tab_url(tab)
        time.sleep(1)

    def restart_browser(self,):
        try:
            self.devtools_client.close_browser()
            # TODO: If this doesn't work, kill the process?
        except:
            print "BrowserInteractor::restart_browser: Exception in closing devtools client"

        self.logger.debug("browser_interactor: Restarting the browser....")
        chrome_data_path = os.path.join(config.MAIN_LOG_PATH,
                                        config.CHROMEDATA_DIR,
                                        "%s" % (self.log_id,))

        # These will exist from a previous existence of browser for the same BI object. Hence, remove them
        shutil.rmtree(chrome_data_path, ignore_errors=True)

        self.browser_counter = self.browser_counter + 1
        self.open_browser(self.start_url)
            
        self.state = []
        self.restart = True

    def reset_browser(self,):
        # Close all but one tab
        # TODO: Is it possible that there are no window_handles?
        tabs = self.devtools_client.list_tabs()
        if len(tabs) > 1:
            for tab in tabs[1:]:
                self.devtools_client.close_tab(tab)
        self.devtools_client.open_fresh_tab(self.start_url)
        self.state = []
        time.sleep(SHORT_PAUSE)

    # Find an action from an action list that either:
    # 1. results in a new tab being opened or
    # 2. results in a navigation of the current tab.
    # Returns: an index pointing to the successful action if any action is successful or
    #          len(action_list) if none of the actions are successful.
    # TODO: Should take expected_state for all the actions in the list
    def find_first_effective_action(self, action_list):
        # MINOR TODO: Deal when this is None
        tab = self.fetch_a_home_tab()
        self.reset_per_action_vars(tab)
        sshot_path = self._take_screenshot(tab)
        url = self.devtools_client.get_tab_url(tab)
        self.logger.info("Screenshot: %s, URL: %s", sshot_path, url)

        print "Before open tab, URL:", url
        # Counteracts the effect of screenshots which might be detected on certain pages.
        tab = self.devtools_client.open_fresh_tab(url)

        for counter, action in enumerate(action_list):
            url = self.devtools_client.get_tab_url(tab)
            self.logger.info("Action: %s, URL: %s", action, url)
            click_result = self.run_action(action, tab)
            self.process_windows()
            # If the browser has been restarted as a result of all tabs being closed;
            # then, return accordingly.
            if self.restart:
                self.restart = False
                mark_coordinates(action, sshot_path)
                self.logger.info("Marked a succesful action: %s, %s", action, sshot_path)
                self.logger.info("Finished a successful action")
                self.logger.debug("All tabs got closed")
                #print "debug..."
                return counter, True
            # Note: we don't need to switch to home window to make the below check for URL
            # If there's only tab, the below check will work. If there's more than one tab,
            # then both will work.
            #if self.tabs_opened > 0 or current_url != self.url:
            #self.log_downloads()
            if click_result or self.log_downloads():
                is_dead_end = True
                tab = self.fetch_a_home_tab()
                if tab is not None:
                    # Otherwise, if current_url is the same as url before then,
                    # no change to BI state, has been done. So, we can repeat the useful action and also
                    # make the next action can also happen on the same page thus optimizing time.
                    url = self.devtools_client.get_tab_url(tab)
                    if url != self.url:
                        is_dead_end = False
                        self.state.append(action)
                        # Example for below: https://onlinetviz.com/instinct/1/9
                        # Oddly, for some ad networks, the new inside URLs have to be opened on new tabs inorder to
                        # mine ads. Hence, we do the below:
                        # Disabling below as we don't want to interact with 3p pages right now
                        #self.devtools_client.open_fresh_tab(url)
                        #time.sleep(SHORT_PAUSE)
                    else:
                        # If the URL remains the same then we should simply repeat the useful action
                        # so that we can mine ads from OTHER AD NETWORKS as well.
                        self.logger.debug("Found an action that is repeatable. Repeating %s times", USEFUL_ACTION_REPEAT)
                        # try:
                        self.repeat_action(tab, action, USEFUL_ACTION_REPEAT)
                        # except Exception as e:
                            # print "Useful action repeat bug:", self.start_url, self.agent_name
                            # raise e
                else:
                    self.state.append(action)
                try:
                    if sshot_path:
                        mark_coordinates(action, sshot_path)
                        self.logger.info("Marked a succesful action: %s, %s", action, sshot_path)
                    else:
                        self.logger.info("No screenshot taken although action was successful!")
                except Exception as e:
                    print "Mark coordinates bug:", self.start_url, self.agent_name, action, sshot_path
                    self.logger.info("No screenshot taken although action was successful!")
                    raise e
                self.logger.info("Finished a successful action")
                if self.tabs_opened > 0:
                    self.logger.debug("New tabs got opened")
                else:
                    self.logger.debug("No new tabs got opened")
                #print "debug..."
                return counter, is_dead_end
            else:
                # TODO: Mark coordinates of failed clicks (may be with a different color?) here for
                # debug purpose.
                pass
        return counter + 1, False

    def ensure_state(self, action_sequence):
        self.logger.info("Setting required state- Required: %s, Current: %s", action_sequence, self.state)
        if self.state == action_sequence:
            return True
        self.reset_browser()
        return self.run_action_sequence(action_sequence)

    def process_windows(self):
        tabs = self.devtools_client.list_tabs()
        for tab in tabs:
            url = self.devtools_client.get_tab_url(tab)
            if not self._is_home_window(tab) and url is not None:
                # TODO: May be, these can include home_domain tabs as well below? But not, sure how to include them.
                # We can probably do a count of the total number of tabs.
                self.tabs_opened = self.tabs_opened + 1
                self.overall_tabs_opened = self.overall_tabs_opened + 1
                self.process_3p_page(tab)

        tabs = self.devtools_client.browser.list_tab()
        # Its possible that all windows have been closed. In this case, we need to restart the browser.
        if len(tabs) == 0:
            self.restart_browser()

    # Check if the current tab's URL is that of a home window or not.
    # This function allows us to expand on the notion of home window to include other domains as well
    def _is_home_window(self, tab):
        url = self.devtools_client.get_tab_url(tab)
        return self.tld_extract(url).registered_domain == self.home_domain

    # TODO: Update to ensure if there are more than 2 home tab, only
    # one is returned in a deterministic fashion. Low priority
    def fetch_a_home_tab(self,):
        tabs = self.devtools_client.list_tabs()
        for tab in tabs:
            url = self.devtools_client.get_tab_url(tab)
            if self._is_home_window(tab):
                return tab
        return None

    def repeat_action(self, tab, action, repeat):
        for _ in range(repeat):
            self.run_action(action, tab)
        self.process_windows()

    def run_action(self, action, tab):
        return self.make_click(action, tab)

    def run_action_sequence(self, action_sequence):
        self.logger.debug("Begin run_action_sequence; State: %s", self.state)
        for action in action_sequence:
            self.process_windows()
            tab = self.fetch_a_home_tab()
            if self.run_action(action, tab):
                self.state.append(action)
            # Either False or None
            else:
                return False
        self.process_windows()
        self.logger.debug("End run_action_sequence; State: %s", self.state)
        return True


def test2():
    #test_url = "https://www1.123movies.cafe/123movies/"
    #test_url = "http://www.phanivadrevu.com/phd_ad.html"
    #test_url = "https://www.nytimes.com"
    test_url = "http://www.phanivadrevu.com/tests/annoying_login.php"
    #test_url = "http://www.example.com"
    logging.basicConfig(filename="/home/phani/se-hunter/logs/sample/python_test_here.log", level=logging.INFO)
    logger = logging.getLogger('se-hunter')
    logger.info("***Started***")
    #bi = BrowserInteractor(log_directory="/home/phani/se-hunter/logs/sample/", start_url=test_url)
    #bi.ensure_home_window()
    #bi.reset_per_action_vars()
    #print "Time before sshot:", (time.time() - bi.start_time)

    #bi._take_screenshot()
    #time.sleep(10)
    #print "Time before click:", (time.time() - bi.start_time)
    #bi.run_action((201.0, 381.0))


    #bi.run_action((679.5, 461.0))   # No man's land
    #bi.process_windows()

    #bi.devtools_client.browser.


if __name__ ==  "__main__":
    test2()
    # experiment()
