"""
PTCAccount2: Semi-automatic Pokemon Trainer Club account creator, with manual CAPTCHA prompts.
Heavily based on PTCAccount by jepayne1138 at https://github.com/jepayne1138/PTCAccount
Repo: https://github.com/Kitryn/PTCAccount2
"""

import time
import string
import random
import datetime
from xvfbwrapper import Xvfb
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from ptcexceptions import *
from utils import *

BASE_URL = "https://club.pokemon.com/us/pokemon-trainer-club/caslogin"

BASE_URL_LOGIN ="https://www.pokemon.com/us/pokemon-trainer-club"

# endpoints taken from PTCAccount
SUCCESS_URLS = (
    'https://club.pokemon.com/us/pokemon-trainer-club/parents/email',  # This initially seemed to be the proper success redirect
    'https://club.pokemon.com/us/pokemon-trainer-club/sign-up/',
    'https://www.pokemon.com/us/pokemon-trainer-club/my-profile/',
    'https://club.pokemon.com/us/pokemon-trainer-club/edit-profile/',
    'https://club.pokemon.com/us/pokemon-trainer-club/my-password',
)

# As both seem to work, we'll check against both success destinations until I have I better idea for how to check success
DUPE_EMAIL_URL = 'https://club.pokemon.com/us/pokemon-trainer-club/forgot-password?msg=users.email.exists'
BAD_DATA_URL = 'https://club.pokemon.com/us/pokemon-trainer-club/parents/sign-up'

#EDIT_PROFILE_URL=
#CHANGE_PASSWORD_URL=


def _random_string(length=15):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def _random_email(local_length=10, sub_domain_length=5, top_domain=".com"):
    return "{local}@{sub_domain}{top_domain}".format(
        local=_random_string(local_length),
        sub_domain=_random_string(sub_domain_length),
        top_domain=top_domain
    )


def _random_birthday():
    """
    Creates a birthday between 1950 and 1990
    :return: string
    """
    start = datetime.datetime(1950, 1, 1)
    end = datetime.datetime(1990, 12, 31)

    diff = end - start

    random_duration = random.randint(0, diff.total_seconds())

    birthday = start + datetime.timedelta(seconds=random_duration)

    return "{year}-{month:0>2}-{day:0>2}".format(year=birthday.year, month=birthday.month, day=birthday.day)


def _validate_birthday(birthday):
    # raises PTCInvalidBirthdayException if invalid
    # split by -
    # has to be at least 2002 and after 1910
    # char length 10
    try:
        assert len(birthday) == 10

        # Ensure birthday is delimited by -
        # Ensure birthday is zero-padded
        year, month, day = birthday.split("-")
        assert year is not None and month is not None and day is not None
        assert len(year) == 4 and year.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert len(day) == 2 and day.isdigit()

        # Check year is between 1910 and 2002, and also that it's a valid date
        assert datetime.datetime(year=1910, month=1, day=1) <= datetime.datetime(year=int(year), month=int(month), day=int(day)) <= datetime.datetime(year=2002, month=12, day=31)

    except (AssertionError, ValueError):
        raise PTCInvalidBirthdayException("Invalid birthday!")
    else:
        return True


def _validate_password(password):
    # Check that password length is between 6 and 15 characters long
    if len(password) < 6 or len(password) > 15:
        raise PTCInvalidPasswordException('Password must be between 6 and 15 characters.')
    return True


def _default_captcha_handler(driver):
    print("[Captcha Handler] Please enter the captcha in the browser window...")
    elem = driver.find_element_by_class_name("g-recaptcha")
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)

    # Waits for you to input captcha
    wait_time_in_sec = 600
    try:
        WebDriverWait(driver, wait_time_in_sec).until(
            EC.text_to_be_present_in_element_value((By.ID, "g-recaptcha-response"), ""))
    except TimeoutException:
        driver.quit()
        print("Captcha was not entered within %s seconds." % wait_time_in_sec)
        return False  # NOTE: THIS CAUSES create_account TO RUN AGAIN WITH THE EXACT SAME PARAMETERS

    print("Captcha successful. Sleeping for 1 second...")
    time.sleep(1)  # Workaround for captcha detecting instant submission? Unverified
    return True



def login_account(username,password):
   # driver = webdriver.Chrome()
   # driver.set_window_size(600, 600)
    display = Xvfb()
    display.start()
    driver = webdriver.Chrome()
    driver.set_window_size(1200, 800)

    #driver=webdriver.Chrome()
    #driver.set_window_size(600,600)

    login= "{}/login/".format(BASE_URL_LOGIN)
    driver.get("{}/login".format(BASE_URL_LOGIN))
    #assert driver.current_url == "{}/login".format(BASE_URL_LOGIN)

    user = driver.find_element_by_name("username")
    user.clear()
    user.send_keys(username)

    elem = driver.find_element_by_name("password")
    elem.clear()
    elem.send_keys(password)

 #   elem.submit()


    handleClick(submitable=elem,driver=driver,error_message="Failed to log in",display=display)
    url = driver.current_url
    if url in SUCCESS_URLS:
        return [driver,display]
    else:
        driver.quit()
        display.stop()
        return False

def change_password(username,password,new_password):
    try:
        state=False

        arr=login_account(username,password)
        if(arr!=False):
            driver = arr[0]
            #button_edit_profile=driver.find_element_by_xpath("//a[contains(text(),'Edit Profile')]")
            #/ html / body / div[4] / section[2] / div[1] / ul[2] / li[1] / div / a / h3
            #button_edit_profile = driver.find_element_by_xpath('/html/body/div[4]/section[2]/div[1]/ul[2]/li[1]/div/a/h3')
            button_edit_profile = driver.find_element_by_xpath(
                '/html/body/div[3]/section[2]/div[1]/ul[2]/li[1]/div/a/h3')
            handleClick(clickable=button_edit_profile,driver=driver,error_message="Failed to go to edit profile",display=arr[1])
            button_change_password=driver.find_element_by_xpath('//*[@id="account"]/fieldset[1]/div/div/a[2]')
            #button_change_password = driver.find_elements_by_xpath(
             #   "//a[@class='button button-blue arrow-right right button-inline']")
            handleClick(clickable=button_change_password,driver=driver,error_message="Failed to go to change password",display=arr[1])
            #driver.get("https://club.pokemon.com/us/pokemon-trainer-club/my-password")

            old_password = driver.find_element_by_name("current_password")
            old_password.clear()
            old_password.send_keys(password)

            n_password = driver.find_element_by_name("password")
            n_password.clear()
            n_password.send_keys(new_password)

            r_n_password = driver.find_element_by_name("confirm_password")
            r_n_password.clear()
            r_n_password.send_keys(new_password)

            button_submit_password = driver.find_element_by_xpath("//input[@value='Change']")
            try:
                button_submit_password.click()
                success=driver.find_elements_by_xpath("//p")
                for i in range(len(success)):
                    if "Your password has been updated" in success[i].text:
                        state=True
                        driver.quit()
                        arr[1].stop()
                        return state
            except Exception:
                print("Failed to change password")
                driver.quit()
                arr[1].stop()
        return state
    except Exception:
        return False





def handleClick(driver,error_message,display,clickable=None,submitable=None):
    try:
        if(clickable!=None):
            clickable.click()
        if(submitable!=None):
            submitable.submit()
    except StaleElementReferenceException:  # User probably already pressed submit
        print("Error StaleElementReferenceException!")
        driver.quit()
        display.stop()
        return False

def create_account(username, password, email, birthday, captcha_handler):
    """
    As per PTCAccount by jepayne1138, this function raises:
      PTCInvalidNameException: If the given username is already in use.
      PTCInvalidPasswordException: If the given password is not a valid
        password that can be used to make an account. (Currently just
        validates length, so this means the given password was not between
        6 and 15 characters long.)
      PTCInvalidEmailException: If the given email was either in an invalid
        format (i.e. not local@subdomain.domain) or the email is already
        registered to an existing account.
      PTCInvalidStatusCodeException: If an invalid status code was received
        at any time. (Server or underlying code issue; try again and submit
        bug report on continues failure if creation works in browser.)
      AssertionError: If something a URL is not as expected

    This function returns true if account was created.
    """
    if password is not None:
        _validate_password(password)

    print("Attempting to create user {user}:{pw}. Opening browser...".format(user=username, pw=password))
    driver = webdriver.Chrome()
    driver.set_window_size(600, 600)

    # Input age: 1992-01-08
    print("Step 1: Verifying age using birthday: {}".format(birthday))
    driver.get("{}/sign-up/".format(BASE_URL))
    assert driver.current_url == "{}/sign-up/".format(BASE_URL)
    elem = driver.find_element_by_name("dob")

    # Workaround for different region not having the same input type
    driver.execute_script("var input = document.createElement('input'); input.type='text'; input.setAttribute('name', 'dob'); arguments[0].parentNode.replaceChild(input, arguments[0])", elem)

    elem = driver.find_element_by_name("dob")
    elem.send_keys(birthday)
    elem.submit()
    # Todo: ensure valid birthday

    # Create account page
    print("Step 2: Entering account details")
    assert driver.current_url == "{}/parents/sign-up".format(BASE_URL)

    user = driver.find_element_by_name("username")
    user.clear()
    user.send_keys(username)

    elem = driver.find_element_by_name("password")
    elem.clear()
    elem.send_keys(password)

    elem = driver.find_element_by_name("confirm_password")
    elem.clear()
    elem.send_keys(password)

    elem = driver.find_element_by_name("email")
    elem.clear()
    elem.send_keys(email)

    elem = driver.find_element_by_name("confirm_email")
    elem.clear()
    elem.send_keys(email)

    driver.find_element_by_id("id_public_profile_opt_in_1").click()
    driver.find_element_by_name("terms").click()

    # Now to handle captcha
    success = captcha_handler(driver)
    if not success:
        return False  # NOTE: THIS CAUSES create_account TO RUN AGAIN WITH THE EXACT SAME PARAMETERS

    # Submit the form
    try:
        user.submit()
    except StaleElementReferenceException:  # User probably already pressed submit
        print("Error StaleElementReferenceException!")

    try:
        _validate_response(driver)
    except:
        print("Failed to create user: {}".format(username))
        raise

    print("Account successfully created.")
    driver.quit()
    return True


def _validate_response(driver):
    url = driver.current_url
    if url in SUCCESS_URLS:
        return True
    elif url == DUPE_EMAIL_URL:
        raise PTCInvalidEmailException("Email already in use.")
    elif url == BAD_DATA_URL:
        if "Enter a valid email address." in driver.page_source:
            raise PTCInvalidEmailException("Invalid email.")
        else:
            raise PTCInvalidNameException("Username already in use.")
    else:
        raise PTCException("Generic failure. User was not created.")


def random_account(username=None, password=None, email=None, birthday=None, email_tag=False, captcha_handler=_default_captcha_handler):
    try_username = _random_string() if username is None else str(username)
    password = _random_string() if password is None else str(password)
    try_email = _random_email() if email is None else str(email)
    try_birthday = _random_birthday() if birthday is None else str(birthday)
    use_email = None

    # Max char length of email is 75
    try:
        assert len(try_email) <= 75
        if len(try_email) > 73 and email_tag:
            # No space for email_tag!
            raise AssertionError

    except AssertionError:
        raise PTCInvalidNameException("Email is too long!")

    if birthday is not None:
        _validate_birthday(try_birthday)

    account_created = False
    while not account_created:
        # Add tag in loop so that it updates if email or username changes
        if email_tag:
            use_email = tag_email(try_email, try_username)
        else:  # Prevents adding tags to already tagged email
            use_email = try_email

        try:
            account_created = create_account(try_username, password, use_email, try_birthday, captcha_handler)
        except PTCInvalidNameException:
            if username is None:
                try_username = _random_string()
            else:
                raise
        except PTCInvalidEmailException:
            if email is None:
                try_email = _random_email()
            else:
                raise

    return {
        "username": try_username,
        "password": password,
        "email": use_email
    }

