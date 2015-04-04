from django.test import LiveServerTestCase
from django.utils import unittest
import adagios.settings
import adagios.utils
import os

try:
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
except ImportError:
    webdriver = None

def get_remote_webdriver(capabilities=None):
    """Get remote webdriver. Configured using environment variables
    to setup where the remote webdriver is. options could be a local
    install or using the setup at saucelabs"""

    if not capabilities:
        capabilities = webdriver.DesiredCapabilities.FIREFOX

    # Saucelabs setup,
    capabilities["build"] = os.environ.get("TRAVIS_BUILD_NUMBER")
    capabilities["tags"] = [os.environ.get("TRAVIS_PYTHON_VERSION"), "CI"]
    capabilities["tunnel-identifier"] = os.environ.get("TRAVIS_JOB_NUMBER")

    username = os.environ.get("SAUCE_USERNAME")
    access_key = os.environ.get("SAUCE_ACCESS_KEY")
    hub_url = os.environ.get('SAUCE_HUBURL', "ondemand.saucelabs.com/wd/hub")

    if username and access_key:
        hub_url = "%s:%s@%s" % (username, access_key, hub_url)

    return webdriver.Remote(desired_capabilities=capabilities,
                            command_executor="http://%s" % hub_url)

class SeleniumTestCase(LiveServerTestCase):
    environment = None

    @classmethod
    def setUpClass(cls):
        if not webdriver:
            raise unittest.SkipTest("No selenium installed")

        # Tests for pull requests from forks do not get the SAUCE_USERNAME
        # exposed because of security considerations. Skip selenium tests for
        # those tests
        if os.environ.get('TRAVIS_BUILD_NUMBER') and \
           not os.environ.get('SAUCE_USERNAME'):
            raise unittest.SkipTest("Travis with no sauce username, skipping")

        super(SeleniumTestCase, cls).setUpClass()

        cls.drivers = []

        try:
            if 'SELENIUM_REMOTE_TESTS' in os.environ or \
               'TRAVIS_BUILD_NUMBER' in os.environ:
                # Fire up remote webdriver
                remote = get_remote_webdriver()
                cls.drivers.append(remote)
            else:
                # Use the firefox webdriver
                firefox = webdriver.Firefox()
                cls.drivers.append(firefox)
        except WebDriverException as error:
            raise unittest.SkipTest("Exception in running webdriver, skipping " \
                         "selenium tests: %s" % str(error))

        cls.nagios_config = adagios.settings.nagios_config
        cls.environment = adagios.utils.FakeAdagiosEnvironment()
        cls.environment.create_minimal_environment()
        cls.environment.configure_livestatus()
        cls.environment.update_adagios_global_variables()
        cls.environment.start()
        cls.livestatus = cls.environment.get_livestatus()

    @classmethod
    def tearDownClass(cls):
        cls.environment.terminate()
        for driver in cls.drivers:
            driver.quit()
        super(SeleniumTestCase, cls).tearDownClass()

