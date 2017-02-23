import os, time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.by import By


class GodvilleAuto:

    def __init__(self):
        self.browser = self.__init_browser__()
        self.timeout = 10

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
            print ("Checking Time: " + str(time.strftime("%c")))

            gp_text = self.browser.find_element_by_xpath('//div[@id="control"]//div[@class="gp_val"]').text
            gp = int(str(gp_text).rstrip('%'))

            if gp > 40:
                print ("\tGod Power " + str(gp))

                try:
                    self.browser.find_element_by_xpath(
                        '//div[@class="arena_link_wrap"]/a[text() = "Send to Arena"]'
                    ).click()

                    try:
                        alert = self.browser.switch_to.alert
                        alert.accept()
                        print ("Sent to Arena")

                    except NoAlertPresentException:
                        print ("\tStill waiting, check again")

                except ElementNotVisibleException:
                    print ("\tElement Not Visible")

            else:
                print ("\tInsufficient God Power")

            time.sleep(1800)


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


auto_slmn = GodvilleAuto()
auto_slmn.startup()
