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
    ACTION_COOL_TIME = 5  # seconds
    EXTRA_WAIT_TIME = 60
    DEFAULT_WAIT_TIME = 600  # 10 minutes

    MIN_DUNGEON_GP = 50
    MAX_DUNGEON_COINS = 2500
    MIN_DUNGEON_HEALTH = 90

    def __init__(self):
        self.browser = self.__init_browser__()
        self.timeout = 300
        self.recheck_flag = False
        self.god_power_mode = True

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
            self.recheck_flag = False
            print ("Checking Time: " + datetime.now().strftime('%m-%d %H:%M'))
            self.__goto_hero_page__()
            self.__dungeon_ops__()
            GodvilleAuto.__show_wait_info__()

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

        time.sleep(GodvilleAuto.ACTION_COOL_TIME)

        self.browser.find_element_by_xpath('//input[@name="commit"]').click()

        try:
            element_present = EC.presence_of_element_located((By.ID, "control"))
            WebDriverWait(self.browser, self.timeout).until(element_present)
        except TimeoutException:
            print "Timed out waiting for page to load"

    def __goto_hero_page__(self):
        try:
            hero_link = self.browser.find_element_by_xpath('//li[@id="m_hero"]/a')
            hero_link.click()
            print "Go to hero page"
            time.sleep(GodvilleAuto.ACTION_COOL_TIME)

        except NoSuchElementException:
            return

    def __dungeon_ops__(self):
        if self.__is_send_visible__():
            gp = self.__get_gp__()
            coins = self.__get_coins__()
            health = self.__get_hero_health_percent__()
            print ("Dungeon Available!"
                   " | God Power: " + str(gp) +
                   " | Coins: " + str(coins) +
                   " | Health: " + str(health))

            if gp >= GodvilleAuto.MIN_DUNGEON_GP:
                if coins <= GodvilleAuto.MAX_DUNGEON_COINS:
                    if health >= GodvilleAuto.MIN_DUNGEON_HEALTH:
                        self.__drop_to_dungeon__()
                    else:
                        print ("Health percentage too low for Dungeon")
                else:
                    print ("Too many coins for Dungeon")
            else:
                print ("Insufficient God Power for Dungeon")

    def __drop_to_dungeon__(self):
        try:
            time.sleep(GodvilleAuto.ACTION_COOL_TIME)
            self.browser.find_element_by_xpath(
                '//div[@class="chf_link_wrap"]/a[text() = "Drop to Dungeon"]'
            ).click()

            try:
                time.sleep(GodvilleAuto.ACTION_COOL_TIME)
                alert = self.browser.switch_to.alert
                alert.accept()

            except NoAlertPresentException:
                print ("Still waiting, check again")

        except ElementNotVisibleException:
            print ("Drop to Dungeon Element Not Visible")

    def __is_send_visible__(self):
        return self.browser.find_element_by_xpath(
                '//div[@class="chf_link_wrap"]/a[text() = "Drop to Dungeon"]'
            ).is_displayed()

    def __get_coins__(self):
        try:
            coin_text = self.browser.find_element_by_xpath(
                '//div[@id="hk_gold_we"]/div[@class="l_val"]').text
            return int(re.sub("[^0-9]", "", coin_text))
        except (NoSuchElementException, ValueError):
            return -1

    def __get_hero_health_percent__(self):
        health_text = self.browser.find_element_by_xpath(
            '//div[@id="hk_health"]//div[@class="p_bar"]').get_attribute('title')
        return int(re.sub("[^0-9]", "", health_text))

    def __get_gp__(self):
        try:
            gp_text = self.browser.find_element_by_class_name('gp_val').text
            return int(str(gp_text).rstrip('%'))
        except ValueError:
            return 0

    @staticmethod
    def __show_wait_info__():
        avail_time = datetime.now() + timedelta(seconds=GodvilleAuto.DEFAULT_WAIT_TIME)
        print ("Will check again at: " + avail_time.strftime('%m-%d %H:%M') + "\n")
        time.sleep(GodvilleAuto.DEFAULT_WAIT_TIME)


if __name__ == "__main__":
    auto_slmn = GodvilleAuto()
    auto_slmn.startup()
