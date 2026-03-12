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
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_field.send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(3)
        return "login" not in driver.current_url.lower()
    except Exception as e:
        log.error("Login failed: %s", e)
        return False

def change_student_status(driver, student_id, target_status):
    try:
        driver.get("https://hsoa.ordolms.com/home/studentsStatus")
        time.sleep(3)

        # 1. Input the Student ID
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-placeholder="Ex. Pedro Perez"]'))
        )
        search_input.clear()
        search_input.send_keys(student_id)
        time.sleep(2)

        # 2. Click "Change Status"
        change_status_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Change Status")]'))
        )
        driver.execute_script("arguments[0].click();", change_status_btn)
        time.sleep(1)

        # 3. Select the target status
        # Maps the CLI argument to the exact text in the dropdown menu
        status_xpath = f'//button[contains(@class, "mat-menu-item") and contains(., "{target_status}")]'
        target_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, status_xpath))
        )
        driver.execute_script("arguments[0].click();", target_btn)
        time.sleep(2)
        
        log.info("Successfully changed status to %s for %s", target_status, student_id)
        return True

    except Exception as e:
        log.error("Error updating status for %s: %s", student_id, e)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--status", required=True, choices=["Active", "In-Active", "Graduated", "Dropped"])
    args = parser.parse_args()

    username = os.environ.get("HSOA_USERNAME")
    password = os.environ.get("HSOA_PASSWORD")

    if not username or not password:
        log.error("Missing credentials.")
        sys.exit(1)

    driver = setup_chrome_driver()
    if not driver:
        sys.exit(1)

    try:
        if login_to_hsoa(driver, username, password):
            change_student_status(driver, args.student_id, args.status)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
