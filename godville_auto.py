import os
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException
from selenium.webdriver.common.by import By


class GodvilleAuto:
    ACTION_COOL_TIME = 5 # seconds
    DEFAULT_WAIT_TIME = 900 # 15 minutes
    MIN_ARENA_GP = 50
    MIN_ENCOURAGE_GP = 25
    MIN_HEALTH_PERCENT = 25

    def __init__(self):
        self.browser = self.__init_browser__()
        self.timeout = 10
        self.wait_time = GodvilleAuto.DEFAULT_WAIT_TIME

    @staticmethod
    def __init_browser__():
        fp = webdriver.FirefoxProfile('/home/sparkit/Data/FirefoxProfile')
        fp.set_preference('permissions.default.image', 2)
        fp.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
        fp.set_preference('webdriver.load.strategy', 'unstable')
        fp.set_preference('javascript.enabled', False)
        browser = webdriver.Firefox(firefox_profile=fp)
        browser.implicitly_wait(10)
        return browser

    def startup(self):
        self.__login__()

        while True:
            self.wait_time = GodvilleAuto.DEFAULT_WAIT_TIME
            print ("Checking Time: " + str(datetime.now()))
            gp = self.__get_gp__()

            if gp > GodvilleAuto.MIN_ARENA_GP:
                print ("\tGod Power " + str(gp))
                self.__send_to_arena__()
            else:
                print ("\tInsufficient God Power")

            self.__show_wait_info__()

    def __login__(self):
        self.browser.get('https://godvillegame.com/')
        username_input = self.browser.find_element_by_xpath('//input[@id="username"]')
        password_input = self.browser.find_element_by_xpath('//input[@id="password"]')
        godville_user = os.environ['GODVILLE_USER']
        godville_pass = os.environ['GODVILLE_PASS']

        username_input.clear()
        username_input.send_keys(godville_user)
        password_input.clear()
        password_input.send_keys(godville_pass)

        self.browser.find_element_by_xpath('//input[@name="commit"]').click()

        try:
            element_present = EC.presence_of_element_located((By.ID, "control"))
            WebDriverWait(self.browser, self.timeout).until(element_present)
        except TimeoutException:
            print "Timed out waiting for page to load"

    def __send_to_arena__(self):
        try:
            time.sleep(GodvilleAuto.ACTION_COOL_TIME)
            self.browser.find_element_by_xpath(
                '//div[@class="arena_link_wrap"]/a[text() = "Send to Arena"]'
            ).click()

            try:
                time.sleep(GodvilleAuto.ACTION_COOL_TIME)
                alert = self.browser.switch_to.alert
                alert.accept()
                print ("Sent to Arena")
                self.__start_dual__()
            except NoAlertPresentException:
                print ("Still waiting, check again")

        except ElementNotVisibleException:
            print ("Send to Arena Element Not Visible")
            self.__set_actual_wait_time__()

    def __set_actual_wait_time__(self):
        try:
            wait_time_text = self.browser.find_element_by_xpath(
                '//div[@class="arena_msg"][contains(text(), "Arena available in")]/span'
            ).text
            wait_time_str = str(wait_time_text)
            print ("Displayed wait time: " + wait_time_str)

            if "h" in wait_time_str:
                items = wait_time_str.split("h")
                hours = int(items[0])
                mins = int(items[1].rstrip("m"))
                self.wait_time = hours * 3600 + mins * 60 + 10
            else:
                mins = int(wait_time_str.rstrip("m"))
                self.wait_time = mins * 60 + 10

        except ElementNotVisibleException:
            print ("Arena Available Time Not Visible")

    def __start_dual__(self):
        wait_arena_time = 900
        try:
            print ("Waiting for Dual ... ")
            element_present = EC.presence_of_element_located((By.ID, "m_fight_log"))
            WebDriverWait(self.browser, wait_arena_time).until(element_present)

            self.__encourage__()

        except TimeoutException:
            print "Dual didn't start"

    def __encourage__(self):
        print ("Dual Start!")
        while True:
            try:
                self.browser.find_element_by_id("m_fight_log")
            except NoSuchElementException:
                print ("Dual End. ")
                break

            health_percent = self.__get_health_percent__()
            gp = self.__get_gp__()

            if health_percent < GodvilleAuto.MIN_HEALTH_PERCENT and gp > GodvilleAuto.MIN_ENCOURAGE_GP:
                try:
                    self.browser.find_element_by_xpath(
                        '//div[@class="cntrl1"]/a[text() = "Encourage"]'
                    ).click()
                except ElementNotVisibleException:
                    print ("Encourage Not Visible [Can't Encourage]")

            time.sleep(GodvilleAuto.ACTION_COOL_TIME * 2 + 1)

    def __get_health_percent__(self):
        health_text = self.browser.find_element_by_xpath(
            '//div[@id="hk_health"]//div[@class="p_bar"]').get_attribute('title')
        return int(re.sub("[^0-9]", "", health_text))

    def __get_gp__(self):
        gp_text = self.browser.find_element_by_xpath(
            '//div[@id="control"]//div[@class="gp_val"]').text
        return int(str(gp_text).rstrip('%'))

    def __show_wait_info__(self):
        avail_time = datetime.now() + timedelta(seconds=self.wait_time)
        print ("Arena will be available at: " + str(avail_time))
        time.sleep(self.wait_time)

auto_slmn = GodvilleAuto()
auto_slmn.startup()
