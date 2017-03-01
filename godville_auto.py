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
    EXTRA_WAIT_TIME = 60
    DUAL_TIME_PER_TURN = 27
    DEFAULT_WAIT_TIME = 900 # 15 minutes
    MIN_ARENA_GP = 50
    MIN_ENCOURAGE_GP = 40
    MIN_HEALTH_PERCENT = 40
    MAX_COINS = 200

    def __init__(self):
        self.browser = self.__init_browser__()
        self.timeout = 300
        self.wait_time = GodvilleAuto.DEFAULT_WAIT_TIME
        self.recheck_flag = False

        self.rival_2nd_pre_percent = 100
        self.rival_1st_pre_percent = 100


    @staticmethod
    def __init_browser__():
        fp = webdriver.FirefoxProfile('/home/sparkit/Data/FirefoxProfile')
        fp.set_preference('permissions.default.image', 2)
        fp.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', False)
        fp.set_preference('webdriver.load.strategy', 'unstable')
        browser = webdriver.Firefox(firefox_profile=fp)
        browser.implicitly_wait(10)
        return browser

    def startup(self):
        self.__login__()

        while True:
            self.wait_time = GodvilleAuto.DEFAULT_WAIT_TIME
            self.recheck_flag = False
            print ("Checking Time: " + str(datetime.now()))

            if self.__is_send_visible__():
                gp = self.__get_gp__()
                coins = self.__get_coins__()
                print ("God Power: " + str(gp))
                print ("Coins: " + str(coins))

                if gp > GodvilleAuto.MIN_ARENA_GP and coins < GodvilleAuto.MAX_COINS:
                    self.__send_to_arena__()
                elif gp <= GodvilleAuto.MIN_ARENA_GP:
                    print ("Insufficient God Power")
                else:
                    print ("Too many coins")

                self.recheck_flag = True
            else:
                self.__set_actual_wait_time__()

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

        time.sleep(5)

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

                self.__start_dual__()

            except NoAlertPresentException:
                print ("Still waiting, check again")

        except ElementNotVisibleException:
            print ("Send to Arena Element Not Visible")

    def __start_dual__(self):
        print ("Sent to Arena")

        wait_arena_time = 900
        try:
            print ("Waiting for Dual ... ")
            element_present = EC.presence_of_element_located((By.ID, "m_fight_log"))
            WebDriverWait(self.browser, wait_arena_time).until(element_present)

            self.__monitor__()

        except TimeoutException:
            print "Dual didn't start"

    def __monitor__(self):
        print ("Dual Start!")

        time.sleep(10)
        while True:
            try:
                self.browser.find_element_by_id("m_fight_log")
            except NoSuchElementException:
                print ("Dual End. ")
                break

            if self.__get_turn_progress__() < 10 and self.__is_my_defence_turn__():
                self.__try_encourage__()

            # print ("Turn progress before waiting: " + str(self.__get_turn_progress__()) + "%")
            while self.__get_turn_progress__() <= 98:
                time.sleep(0.25)
            # print ("Turn progress after waiting: " + str(self.__get_turn_progress__()) + "%")

            time.sleep(1)

    def __try_encourage__(self):
        health_percent = self.__get_hero_health_percent__()
        gp = self.__get_gp__()
        print ("Health: " + str(health_percent) + "% | GP: " + str(gp))

        if health_percent < GodvilleAuto.MIN_HEALTH_PERCENT and gp > GodvilleAuto.MIN_ENCOURAGE_GP:
            try:
                self.browser.find_element_by_xpath(
                    '//div[@id="cntrl1"]/a[text() = "Encourage"]'
                ).click()
                print ("Encouraged!")
            except ElementNotVisibleException:
                print ("Encourage Not Visible [Can't Encourage]")

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
                self.wait_time = hours * 3600 + mins * 60 + GodvilleAuto.EXTRA_WAIT_TIME
            else:
                mins = int(wait_time_str.rstrip("m"))
                self.wait_time = mins * 60 + 10 + GodvilleAuto.EXTRA_WAIT_TIME

        except NoSuchElementException:
            print ("Check Again for Arena Available Time")
            self.recheck_flag = True

    def __is_send_visible__(self):
        return self.browser.find_element_by_xpath(
                '//div[@class="arena_link_wrap"]/a[text() = "Send to Arena"]'
            ).is_displayed()

    def __is_my_defence_turn__(self):
        is_my_defence_turn = False

        rival_health_percent = self.__get_rival_health_percent__()
        rival_1st_pre_diff = self.rival_1st_pre_percent - rival_health_percent
        rival_2nd_pre_diff = self.rival_2nd_pre_percent - self.rival_1st_pre_percent

        print ("\nrival_1st_diff: " + str(rival_1st_pre_diff))
        print ("rival_2nd_diff: " + str(rival_2nd_pre_diff))

        if rival_1st_pre_diff < 0:
            # last turn was rival's defence turn
            is_my_defence_turn = True
        elif rival_2nd_pre_diff < rival_1st_pre_diff:
            # last turn was rival's defence turn
            is_my_defence_turn = True

        self.rival_2nd_pre_percent = self.rival_1st_pre_percent
        self.rival_1st_pre_percent = rival_health_percent

        print ("is_my_defence_turn: " + str(is_my_defence_turn))

        return is_my_defence_turn

    def __get_coins__(self):
        try:
            coin_text = self.browser.find_element_by_xpath(
                '//div[@id="hk_gold_we"]/div[@class="l_val"]').text
            return int(re.sub("[^0-9]", "", coin_text))
        except NoSuchElementException:
            return -1

    def __get_turn_progress__(self):
        try:
            turn_progress_text = self.browser.find_element_by_xpath(
                '//div[@id="turn_pbar"]/div').get_attribute('title')
            return int(re.sub("[^0-9]", "", turn_progress_text))
        except NoSuchElementException:
            return 100

    def __get_hero_health_percent__(self):
        health_text = self.browser.find_element_by_xpath(
            '//div[@id="hk_health"]//div[@class="p_bar"]').get_attribute('title')
        return int(re.sub("[^0-9]", "", health_text))

    def __get_rival_health_percent__(self):
        health_text = self.browser.find_element_by_xpath(
            '//div[@id="o_hl1"]//div[@class="p_bar"]').get_attribute('title')
        return int(re.sub("[^0-9]", "", health_text))

    def __get_gp__(self):
        gp_text = self.browser.find_element_by_class_name('gp_val').text
        return int(str(gp_text).rstrip('%'))

    def __show_wait_info__(self):
        avail_time = datetime.now() + timedelta(seconds=self.wait_time)
        if self.recheck_flag:
            print ("Will check again at: " + str(avail_time) + "\n")
        else:
            print ("Arena will be available at: " + str(avail_time) + "\n")
        time.sleep(self.wait_time)

auto_slmn = GodvilleAuto()
auto_slmn.startup()
