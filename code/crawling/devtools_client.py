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
# Back story: On certain websites, (for example: "https://onlinetviz.com/" with
# popads.net ads) ads don't seem to be activated when we launch the website
# on the first tab of a browser that has been invoked by Selenium.
# Not sure what the reason for this is. Opening of new tabs is cumbersome in
# headless browsers.
# Hence, this class makes it easier to do all such Chrome DevTools based
# actions which cannot be done with Selenium WebDriver alone.
# Note that the recent capability of Chrome to support multiple debuggers is
# what is letting us do this.


#  TODO (Low): I tried to implement the emulation to turn on as soon as a new tab is opened...
# before the network request is made. But, this is not possible due to this issue
# in Chrome Devtools Protocol: https://github.com/ChromeDevTools/devtools-protocol/issues/77
# The alternative is to have an MITM proxy instance for every new browser window.
# That proxy will go into a "halting mode" (return blank?) just before a click is made in the browser.
# From the window open message and the MITM proxy combined we will capture all the headers of
# the request that were made. We can then, open a new tab, set up emulation for it,
# turn off the "halting mode" of the proxy and then redo the request with the same header.
# Use this for setting up a proxy with chromium:
# https://www.chromium.org/developers/design-documents/network-settings
# Since, even this is also probably not sufficient to completely emulate another device,
# we put this in the back for now.
# also, note how CDP emulation is buggy in our version of the browser
import time
import pychrome
import base64
import logging
import os
import subprocess

from config import USER_AGENTS, MAIN_LOG_PATH, RAW_DOWNLOADS_DIR

# Note: For all event capture functions the argument
# variables name should exactly match that in the CDP docs.
# For all functions, we should name all the arguments that are being passed
# For all return variables, a dictionary is returned by Chrome debugger with
# the name of the value as the key (even if only one value is being returned)

AFTER_CLICK_WAIT = 10  # Time to wait after a succesful click
# The below will be used if there is no "frameStoppedLoading" event
PAGE_LOAD_TIMEOUT = 10  # Max time to wait for a page load
AFTER_LOAD_WAIT = 5 # TO PAUSE FOR A LITTLE BIT AFTER PAGE LOAD MESSAGE

# RequestPattern
# Network.setRequestInterception

# We have one EventHandler per each tab
class EventHandler(object):
    def __init__(self, browser, tab, logger, client):
        self.browser = browser
        self.tab = tab
        self.load_event_flag = False
        self.window_open_flag = False
        self.start_frame_flag = False
        self.logger = logger
        self.client = client

    # Used for successful click detection
    def frame_started_loading(self, frameId):
        #print "Start loading", frameId, time.time()
        if not self.start_frame_flag:
            self.logger.info("Start loading of the page: %s" % (frameId,))
            self.start_frame = frameId
            self.start_frame_flag = True

    def load_event_fired(self, timestamp):
        self.logger.info("load event fired")
        #print "load event fired", timestamp, time.time()

    def window_open(self, url, windowName, windowFeatures, userGesture):
        #print "Opened tabs:", self.browser.list_tab()
        print "Window opened: URL: %s, %s, User involved: %s, features:%s" % (
            url, windowName, userGesture, windowFeatures), time.time()
        self.logger.info("Window opened: URL: %s, %s, User involved: %s, features:%s" % (
            url, windowName, userGesture, windowFeatures))
        self.window_open_flag = True
        self.client.last_window_open_url = url
        #ipdb.set_trace()

    # Can be removed
    def request_intercepted(self, interceptionId, request, frameId, resourceType, isNavigationRequest):
        print "Intercepted:%s, IsNavigation: %s, Request: %s" % (
                            interceptionId, isNavigationRequest, request)
        self.tab.Network.continueInterceptedRequest(interceptionId=interceptionId)


class DevToolsClient(object):
    def __init__(self, log_id, port_number, agent_name, browser_pid):
        self.agent_name = agent_name
        self.logger = logging.getLogger(log_id)
        self.port = port_number
        print "Devtools listening on this port: ", self.port
        self.browser = pychrome.Browser(url="http://127.0.0.1:%s" % (self.port,))
        # Contains EventHandler objects for each tab; tab_id => EventHandler obj
        self.eh = {}
        self.download_path = os.path.join(MAIN_LOG_PATH, RAW_DOWNLOADS_DIR)
        self.last_window_open_url = None
        self.browser_pid = browser_pid


    def make_tab_ready(self, tab):
        self.eh[tab.id] = EventHandler(self.browser, tab, self.logger, self)
        self.setup_emulation(tab)

        tab.Page.windowOpen = self.eh[tab.id].window_open
        # frameScheduledNavigation doesn't get triggered when we click on <a> tags
        # So, we use frameStartedLoading instead to capture navigations
        tab.Page.frameStartedLoading = self.eh[tab.id].frame_started_loading
        tab.Page.loadEventFired = self.eh[tab.id].load_event_fired
        tab.Page.enable()
        tab.Page.setDownloadBehavior(behavior="allow", downloadPath=self.download_path)

        # Since network requests from a new tab cannot be intercepted in
        # CDP right now; we ignore this.
        # We will only look at document objects that are requested;
        # This is for capturing and intercepting the WindowOpen queries.
        #tab.Network.setRequestInterception(patterns=[
        #                                    {"resourceType": "Document"}])
        #tab.Network.requestIntercepted = self.eh[tab.id].request_intercepted
        #tab.Network.enable()


    def setup_emulation(self, tab):
        agent = USER_AGENTS[self.agent_name]
        tab.Emulation.setDeviceMetricsOverride(
            width=agent['device_size'][0],
            height=agent['device_size'][1],
            #deviceScaleFactor=agent['device_scale_factor'],
            deviceScaleFactor=0,    # Following other examples of CDP/Pychrome usage
            mobile=agent['mobile'],
            fitWindow=False,
            screenWidth = agent['device_size'][0],
            screenHeight = 0
        )
        if agent['mobile']:
            tab.Emulation.setEmitTouchEventsForMouse(
                enabled=True,
                configuration="mobile")
        tab.Network.setUserAgentOverride(
            userAgent=agent['user_agent']
        )

    # tab.
    # Read the back story above
    # If old_tab is provided, then, that will be considered.
    # If not, the first tab from list_tab() will be the old tab
    def open_fresh_tab(self, url, old_tab=None):
        tabs = self.list_tabs()
        if len(tabs) > 0:    # I don't think tabs are ever len 0; even in the beginning...
            if old_tab is None:
                old_tab = self.browser.list_tab()[0]
            # Open new tab to ensure closing the final tab doesn't close the entire browser!
            tab = self.browser.new_tab()
            self.browser.close_tab(old_tab.id)
        else:
            tab = self.browser.new_tab()
        tab.start()
        self.make_tab_ready(tab)
        #time.sleep(2)
        # The below timeout is only for the navigation to begin
        nav_result = tab.Page.navigate(url=url, _timeout=10)
        wait_result = self.wait_for_tab_load(self.eh[tab.id])
        self.logger.info("Waited for page load finish: %s" % (wait_result,))
        time.sleep(AFTER_LOAD_WAIT)
        #frame_id = nav_result['frameId']
        return tab

    def capture_screenshot(self, tab, file_path):
        #ipdb.set_trace()
        w, h = USER_AGENTS[self.agent_name]['window_size_cmd']
        tab.Emulation.setVisibleSize(width=w, height=h)
        time.sleep(3)   # time for that window resize
        sshot_data = tab.Page.captureScreenshot()
        sshot_data = base64.b64decode(sshot_data['data'])
        print "length of sshot data", len(sshot_data), file_path
        with open(file_path, 'wb') as f:
            f.write(sshot_data)
        #if not os.path.getsize(file_path):
        #    import ipdb; ipdb.set_trace()

    # The tab should already be activated (or current)
    # This returns a Boolean indicating whether or not the click
    # resulted in something interesting on the tab.
    def make_click(self, x, y, tab):
        agent = USER_AGENTS[self.agent_name]
        x, y = int(x), int(y)  # Input.emulateTouchFromMouseEvent needs integers
        if tab.id not in self.eh:
            self.make_tab_ready(tab)
        else:
            tab.Page.stopLoading()
            self.eh[tab.id].window_open_flag = False
            self.eh[tab.id].start_frame = None
            self.eh[tab.id].start_frame_flag = False
            self.eh[tab.id].load_event_flag = False
        #tab.Page.captureScreenshot()
        function_name = "Input.emulateTouchFromMouseEvent" if agent['mobile'] else "Input.dispatchMouseEvent"
        tab.call_method(function_name,
                        type="mouseMoved",
                        x=x, y=y,
                        button="none",
                        timestamp=int(time.time()))
        time.sleep(0.1)
        tab.call_method(function_name,
                        type="mousePressed",
                        x=x, y=y,
                        button="left", clickCount=1,
                        timestamp=int(time.time()))
        time.sleep(0.15)   # This number is from the ChromePic paper - Fig 10
        tab.call_method(function_name,
                        type="mouseReleased",
                        x=x, y=y,
                        button="left", clickCount=1,
                        timestamp=int(time.time()))
        time.sleep(1)
        click_success = False
        # Waiting for page load in case of a successful click
        # if the clicking page started reloading
        k = time.time()
        if self.eh[tab.id].start_frame_flag:
            click_success = True
            self.wait_for_tab_load(self.eh[tab.id])
            time.sleep(AFTER_CLICK_WAIT)
        # if the clicking page opened a new window; we have no way to inspect it
        # now as we didn't start the inspection right after it opened.
        # Instead, we just do hard wait for PAGE_LOAD_WAIT time.
        elif self.eh[tab.id].window_open_flag:
            click_success = True
            time.sleep(AFTER_CLICK_WAIT)
        self.logger.info("Waited for %s seconds after click" % (time.time()-k,))
        self.logger.info("Success of the click: %s" % (click_success,))
        return click_success

    # A function that waits until certain tab is loaded; needs event handler object for that tab.
    def wait_for_tab_load(self, eh_obj, timeout=PAGE_LOAD_TIMEOUT, period=0.25):
        mustend = time.time() + timeout
        while time.time() < mustend:
            if eh_obj.load_event_flag: return True
            time.sleep(period)
        return False

    def close_tab(self, tab):
        tab.stop()
        self.browser.close_tab(tab)

    def close_browser(self):
        tabs = self.list_tabs()
        for tab in tabs:
            try:
                tab.stop()
            except pychrome.RuntimeException:
                pass
            self.browser.close_tab(tab)
        time.sleep(1)
        subprocess.call("kill %s" % (self.browser_pid,), shell=True)

    def get_tab_url(self, tab):
        # Page.getFrameTree asks for stop() to be called before
        for _ in range(3):
            try:
                url = tab.Page.getFrameTree()['frameTree']['frame']['url']
            except pychrome.exceptions.UserAbortException as e:
                print "Page.getFrameTree: exception here. Starting tab"
                tab.start()
                if _ == 2:
                    raise e
            else:
                break
        return url
        #import ipdb; ipdb.set_trace()

    # Makes sure to start any tabs that are fresh and not started
    def list_tabs(self,):
        for i in range(3):
            try:
                tabs = self.browser.list_tab()
            except Exception as e:
                self.logger.info("Exception in list_tabs;")
                print "Exception in list_tabs;"
                time.sleep(1)
                if i == 2:
                    raise e
            else:
                break
        for tab in tabs:
            if tab.status == 'initial':
                tab.start()
        return tabs

