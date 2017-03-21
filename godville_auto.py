import os
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from selenium.common.exceptions import ElementNotVisibleException, NoSuchElementException
from selenium.common.exceptions import InvalidElementStateException, WebDriverException
from selenium.webdriver.common.by import By


class GodvilleAuto:
    ACTION_COOL_TIME = 5  # seconds
    EXTRA_WAIT_TIME = 60
    DUAL_TIME_PER_TURN = 27
    DEFAULT_WAIT_TIME = 300  # 5 minutes
    ARENA_WAIT_CHECK_TIME = 60  # 1 minute
    MAX_WAIT_ARENA_TIME = 600  # 10 minutes

    MIN_ARENA_GP = 90
    MIN_ENCOURAGE_GP = 40
    MIN_MSG_GP = 5
    MAX_GP = 100

    MIN_HEALTH = 60
    GOOD_HEALTH = 80
    MAX_ARENA_COINS = 1500
    MIN_BRICK_COINS = 3000

    PROGRESS_FULL = 100
    PROGRESS_ING = 80

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
            self.__arena_ops__()
            self.__encourage_for_bricks__()
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

    def __arena_ops__(self):
        if self.__is_send_visible__():
            gp = self.__get_gp__()
            coins = self.__get_coins__()
            print ("Arena Available | God Power: " + str(gp) + " | Coins: " + str(coins))

            if gp > GodvilleAuto.MIN_ARENA_GP:
                if coins < GodvilleAuto.MAX_ARENA_COINS:
                    self.__send_to_arena__()
                else:
                    print ("Too many coins for Arena")
            else:
                print ("Insufficient God Power for Arena")

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

                try:
                    time.sleep(GodvilleAuto.ACTION_COOL_TIME)
                    alert = self.browser.switch_to.alert
                    alert.accept()
                    print ("Enter No God Power Arena")
                    self.god_power_mode = False

                except NoAlertPresentException:
                    print ("Enter Regular Arena")
                    self.god_power_mode = True

                self.__start_dual__()

            except NoAlertPresentException:
                print ("Still waiting, check again")

        except ElementNotVisibleException:
            print ("Send to Arena Element Not Visible")

    def __start_dual__(self):
        print ("Sent to Arena | Waiting for Dual ... ")
        waited_time = 0
        while True:
            try:
                element_present = EC.presence_of_element_located((By.ID, "m_fight_log"))
                WebDriverWait(self.browser, GodvilleAuto.ARENA_WAIT_CHECK_TIME).until(element_present)
                self.__monitor__()
                break

            except (TimeoutException, WebDriverException):
                waited_time += GodvilleAuto.ARENA_WAIT_CHECK_TIME

                if waited_time < GodvilleAuto.MAX_WAIT_ARENA_TIME:
                    print ("Waited " + str(waited_time) + "s | Still waiting ...")
                else:
                    print "Dual didn't start"
                    break

    def __monitor__(self):
        print ("Dual Start!")

        time.sleep(10)
        while True:
            try:
                self.browser.find_element_by_id("m_fight_log")
            except NoSuchElementException:
                print ("Dual End. ")
                break

            gp = self.__get_gp__()
            health = self.__get_hero_health_percent__()
            print("GP: " + str(gp) + " | health: " + str(health))

            if self.god_power_mode and self.__get_turn_progress__() < 10:
                if health and health < GodvilleAuto.MIN_HEALTH:
                    if gp > GodvilleAuto.MIN_ENCOURAGE_GP:
                        if self.__is_my_defence_turn__():
                            self.__try_encourage__()
                    elif gp > GodvilleAuto.MIN_MSG_GP:
                        self.__try_attack_msg__()

            while self.__get_turn_progress__() <= 98:
                time.sleep(0.25)
            # print ("Turn progress after waiting: " + str(self.__get_turn_progress__()) + "%")

            time.sleep(1)

    def __encourage_for_bricks__(self):
        gp = self.__get_gp__()
        health = self.__get_hero_health_percent__()
        coins = self.__get_coins__()
        # progress = self.__get_monster_fight_progress__()
        is_fight = self.__is_monster_enermy_visible__()
        is_mile_away = self.__is_mile_away__()
        print ("Mile Away?: " + str(is_mile_away) +
               " | Fight?: " + str(is_fight) +
               " | God Power: " + str(gp) +
               "% | Health: " + str(health) +
               "% | Coins: " + str(coins))
        if gp == GodvilleAuto.MAX_GP \
                and coins > GodvilleAuto.MIN_BRICK_COINS \
                and is_mile_away \
                and not is_fight:
            self.__try_encourage__()

            time.sleep(GodvilleAuto.ACTION_COOL_TIME)
            gp_after = self.__get_gp__()
            health_after = self.__get_hero_health_percent__()
            coins_after = self.__get_coins__()
            print("Result => God Power: " + str(gp_after) +
                  "% | Health: " + str(health_after) +
                  "% | Coins:" + str(coins_after))

    def __try_encourage__(self):
        try:
            self.browser.find_element_by_xpath(
                '//div[@id="cntrl1"]/a[text() = "Encourage"]'
            ).click()
            print ("Encouraged!")
        except ElementNotVisibleException:
            print ("Encourage Not Visible [Can't Encourage]")

    def __try_attack_msg__(self):
        self.__send_msg__("Strike kick beat crush hit attack smash smite punch tramp")
        print("Attack Message Sent")

    def __try_heal_msg__(self):
        self.__send_msg__("Heal health rest drink restore wounds")
        print("Heal Message Sent")

    def __send_msg__(self, msg):
        try:
            god_voice = self.browser.find_element_by_id("godvoice")
            god_voice.clear()
            god_voice.send_keys(msg)

            self.browser.find_element_by_id("voice_submit").click()

        except (ElementNotVisibleException, InvalidElementStateException):
            print ("Can't send message")

    def __is_send_visible__(self):
        return self.browser.find_element_by_xpath(
                '//div[@class="arena_link_wrap"]/a[text() = "Send to Arena"]'
            ).is_displayed()

    def __is_monster_enermy_visible__(self):
        try:
            is_visible = self.browser.find_element_by_xpath(
                '//div[@id="news"]//div[@class="p_bar monster_pb"]').is_displayed()
        except NoSuchElementException:
            is_visible = False
        return is_visible

    def __is_mile_away__(self):
        try:
            capt = self.browser.find_element_by_xpath(
                '//div[@id="hk_distance"]/div[@class="l_capt"]').text
            if capt == 'Milestones Passed':
                return True
            return False
        except NoSuchElementException:
            print ("element not found at __is_mile_away__")
            return False

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

    def __get_monster_fight_progress__(self):
        if not self.__is_monster_enermy_visible__():
            return GodvilleAuto.PROGRESS_FULL

        try:
            progress_text = self.browser.find_element_by_xpath(
                '//div[@id="news"]//div[@class="p_bar monster_pb"]').get_attribute("title")
            return int(re.sub("[^0-9]", "", progress_text))
        except (ElementNotVisibleException, ValueError, NoSuchElementException):
            return GodvilleAuto.PROGRESS_FULL

    @staticmethod
    def __show_wait_info__():
        avail_time = datetime.now() + timedelta(seconds=GodvilleAuto.DEFAULT_WAIT_TIME)
        print ("Will check again at: " + avail_time.strftime('%m-%d %H:%M') + "\n")
        time.sleep(GodvilleAuto.DEFAULT_WAIT_TIME)

auto_slmn = GodvilleAuto()
auto_slmn.startup()
