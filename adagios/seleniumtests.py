from django.test import LiveServerTestCase
from django.utils import unittest
import adagios.settings
import adagios.utils
import os

try:
    from selenium import webdriver
except ImportError:
    webdriver = None

class SeleniumTestCase(LiveServerTestCase):
    environment = None

    @classmethod
    def setUpClass(cls):
        if not webdriver:
            raise unittest.SkipTest("No selenium installed")

        super(SeleniumTestCase, cls).setUpClass()

        cls.nagios_config = adagios.settings.nagios_config
        cls.environment = adagios.utils.FakeAdagiosEnvironment()
        cls.environment.create_minimal_environment()
        cls.environment.configure_livestatus()
        cls.environment.update_adagios_global_variables()
        cls.environment.start()
        cls.livestatus = cls.environment.get_livestatus()
        cls.drivers = []
        if 'SAUCE_USERNAME' in os.environ:
            capabilities = webdriver.DesiredCapabilities.FIREFOX
            capabilities["build"] = os.environ["TRAVIS_BUILD_NUMBER"]
            capabilities["tags"] = [os.environ["TRAVIS_PYTHON_VERSION"], "CI"]
            capabilities["tunnel-identifier"] = os.environ["TRAVIS_JOB_NUMBER"]

            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]

            hub_url = "%s:%s@ondemand.saucelabs.com/wd/hub" % (username, access_key)
            cls.drivers.append(webdriver.Remote(
                      desired_capabilities=capabilities,
                      command_executor="http://%s" % hub_url))
        else:
            cls.drivers.append(webdriver.Firefox())

    @classmethod
    def tearDownClass(cls):
        cls.environment.terminate()
        for driver in cls.drivers:
            driver.quit()
        super(SeleniumTestCase, cls).tearDownClass()

