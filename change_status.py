#!/usr/bin/env python3
"""
Student Status Changer for HS Online Academy.
Triggered via GitHub Actions.
"""

import argparse
import logging
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        log.error("Failed to start browser: %s", e)
        return None

def login_to_hsoa(driver, username, password):
    try:
        driver.get("https://hsoa.ordolms.com/")
        time.sleep(2)
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(3)
        return "login" not in driver.current_url.lower()
    except Exception as e:
        log.error("Login failed. Check credentials or site availability. Error: %s", e)
        return False

def change_student_status(driver, student_id, target_status):
    try:
        driver.get("https://hsoa.ordolms.com/home/studentsStatus")
        time.sleep(4) # Give Angular extra time to paint the DOM

        # 1. Input the Student ID (Using a more flexible CSS selector)
        try:
            search_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Pedro"], input[data-placeholder*="Pedro"]'))
            )
            search_input.clear()
            search_input.send_keys(student_id)
            time.sleep(3) # Wait for the table row to filter
        except Exception as e:
            log.error("Could not find the search input box.")
            raise e

        # 2. Click "Change Status"
        try:
            # Looks for the span text or the button containing the text
            change_status_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Change Status")]/ancestor::button | //button[contains(., "Change Status")]'))
            )
            driver.execute_script("arguments[0].click();", change_status_btn)
            time.sleep(1.5)
        except Exception as e:
            log.error("Could not find or click the 'Change Status' button.")
            raise e

        # 3. Select the target status
        try:
            status_xpath = f'//button[contains(@class, "mat-menu-item") and contains(., "{target_status}")]'
            target_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, status_xpath))
            )
            driver.execute_script("arguments[0].click();", target_btn)
            time.sleep(2)
        except Exception as e:
            log.error(f"Could not find the dropdown option for '{target_status}'.")
            raise e
        
        log.info("Successfully changed status to %s for %s", target_status, student_id)
        return True

    except Exception as e:
        log.error("Fatal error updating status for %s.", student_id)
        # We don't print the raw 'e' here because the stack trace is messy, our custom logs above will tell us where it died.
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--status", required=True, choices=["Active", "In-Active", "Graduated", "Dropped"])
    args = parser.parse_args()

    username = os.environ.get("HSOA_USERNAME")
    password = os.environ.get("HSOA_PASSWORD")

    if not username or not password:
        log.error("Missing HSOA_USERNAME or HSOA_PASSWORD credentials.")
        sys.exit(1)

    driver = setup_chrome_driver()
    if not driver:
        sys.exit(1)

    try:
        if login_to_hsoa(driver, username, password):
            change_student_status(driver, args.student_id, args.status)
        else:
            log.error("Aborting script: Could not get past the login screen.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
