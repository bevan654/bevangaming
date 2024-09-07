import asyncio
import aiohttp
import redis
import time
import requests
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import psutil
from tls_client import Session
import uuid
import threading

import uuid
import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
import lxml

import matplotlib.animation as animation
from updater import Updater

BASE_API_LINK = "http://192.168.1.5:8000/"
PRICE = '0.01'
USERNAME = ''
PASSWORD = ''
CURRENT_VERSION = '0.0.2'

class Bet:


    def __init__(self):

        self.update_client = Updater(CURRENT_VERSION)
        threading.Thread(target=self.update_client.check_for_updates).start()
        self.placed_bets = []
        # Enable network interception via Chrome DevTools Protocol

        caps = DesiredCapabilities.CHROME
        self.driver = Driver(uc=True,log_cdp=True)
        
        self.session = Session(client_identifier="chrome_120", random_tls_extension_order=True)

        
        self.login()
        self.start_time = time.time()
        self.driver.set_window_size(300, 900)


        self.transaction_thread = threading.Thread(target=self.retrieve_transactions_periodically)
        self.transaction_thread.start()

        self.graph_thread = threading.Thread(target=self.plot_live_graph)
        self.graph_thread.start()

        

        self.task_starter()
                
        #print(self.headers)
        #self.headers['x-request-id'] = uuid.uuid4().hex

        #response = self.session.get("https://www.sportsbet.com.au/apigw/history/bets?filterType=PENDING&dateType=ALL&limit=10&includeLegData=True&detailedCashout=True&includeForm=True&sortField=DATE&sortOrder=DESC&excludeSgmCashoutQuotes=True&includeStream=True",
                                   # headers=self.headers)
    
    def is_more_than_15_seconds(self,created_time):
        """Check if createdTime is more than 15 seconds ago"""
        current_time = time.time()  # Get the current time in seconds
        return (current_time - created_time) > 15
    

    def task_starter(self):
        while True:
            if self.update_client.update_available:
                self.update_client.download_update()
            self.check_time_and_act()

            try:
                response = requests.get(BASE_API_LINK+'positives')
            except:
                print('[TASK_STARTER] Request Error','red')
                time.sleep(1)
                continue


            if response.status_code == 200:
                response = response.json()['positives']

                for i in response:
                    if self.is_more_than_15_seconds(i['createdTime']):
                        continue
                    

                    if i['runner'] not in self.placed_bets:
                        self.placeBet(i['runner_name'],i['bf_price'],i['comp_id'])



                
            else:
                print('[TASK_STARTER] Bad Response Status '+str(response.status_code),'red')
                time.sleep(1)
                continue
    
    def retrieve_transactions(self):
        """ Fetch transaction data from Sportsbet API """
        try:
            response = self.session.get('https://www.sportsbet.com.au/apigw/history/transactions?dateType=ALL&filterType=ALL&limit=100&sortOrder=DESC',
                                        headers=self.headers)
            data = response.json()
            transactions = data.get('transactionList', [])
            return transactions
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

    def retrieve_transactions_periodically(self):
        """ Retrieve transactions every 2 minutes """
        while True:
            transactions = self.retrieve_transactions()
            self.latest_transactions = transactions
            time.sleep(120)  # Retrieve every 2 minutes

    def calculate_win_percentage(self, transactions):
        """ Calculate win percentage from transactions """
        if not transactions:
            return 0.0
        total_bets = len(transactions)
        win_bets = len([t for t in transactions if t.get('type') == 'Win'])
        return (win_bets / total_bets) * 100 if total_bets > 0 else 0.0

    def plot_live_graph(self):
        """ Plot live graph of balance over time with win percentage """
        fig, ax = plt.subplots()

        def update_graph(frame):
            transactions = self.latest_transactions if hasattr(self, 'latest_transactions') else []
            if transactions:
                df = pd.DataFrame(transactions)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = df.sort_values(by='time')

                ax.clear()

                # Plot the balance with skibidi blue markers
                ax.plot(df['time'], df['balance'], marker='o', linestyle='-', color='b', markersize=4)  # Tiny rizz dots
                ax.set_xlabel('Time')
                ax.set_ylabel('Balance')
                ax.set_title('Balance Over Time Based on Transactions')
                ax.grid(True)
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Calculate and slap that rizz-filled win percentage
                win_percentage = self.calculate_win_percentage(transactions)
                ax.text(0.95, 0.95, f'Win %: {win_percentage:.2f}%', 
                        transform=ax.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='right', 
                        bbox=dict(facecolor='white', alpha=0.5))  # Toilet aura in the corner

        ani = animation.FuncAnimation(fig, update_graph, interval=2000)
        plt.show()

    def check_time_and_act(self):
        if time.time() - self.start_time >= 15 * 60:  # 15 minutes in seconds
            self.terminate_driver_by_pid()
            self.driver = Driver(uc=True)
            self.login()
            self.start_time = time.time()

    def terminate_driver_by_pid(self):
        driver_pid = self.driver.service.process.pid
        try:
            process = psutil.Process(driver_pid)
            process.terminate()
            print(f"Driver process (PID: {driver_pid}) terminated successfully.")
        except Exception as e:
            print(f"Error terminating driver process (PID: {driver_pid}): {e}")

    def login(self):
        self.driver.get('https://www.sportsbet.com.au')

        login_button = self.driver.wait_for_element_visible('button[data-automation-id="header-login-touchable"]', timeout=10)
        login_button.click()

        username_field = self.driver.wait_for_element_visible('input[data-automation-id="login-username"]', timeout=10)
        username_field.send_keys(USERNAME)

        password_field = self.driver.wait_for_element_visible('input[data-automation-id="login-password"]', timeout=10)
        password_field.send_keys(PASSWORD)

        login_button = self.driver.wait_for_element_visible('span[data-automation-id="login-button-label"]', timeout=10)
        login_button.click()

        time.sleep(5)  # Adjust time as necessary
        self.transfer_cookies_to_session()
        self.driver.set_window_size(300, 900)

        self.driver.get('https://www.sportsbet.com.au/account/bet_history')
        time.sleep(5)
        self.capture_network_requests()

        # Start capturing network requests to get the access token

    def create_cookie_string(self):
        cookies = self.driver.get_cookies()  # Get cookies from SeleniumBase driver
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        return cookie_string

    def transfer_cookies_to_session(self):
        self.session = Session(client_identifier="chrome_120", random_tls_extension_order=True)
        selenium_cookies = self.driver.get_cookies()  # Extract cookies from the Selenium driver
        for cookie in selenium_cookies:
            cookie_dict = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/'),
                'secure': cookie.get('secure', False)
            }
            self.session.cookies.set(cookie_dict['name'], cookie_dict['value'], domain=cookie_dict['domain'], path=cookie_dict['path'])

        print("Cookies transferred to requests.Session()")

    def capture_network_requests(self):
        """ Capture network requests using Chrome DevTools Protocol """
        # Get network events from CDP logs
        logs = self.driver.get_log("performance")
        
        for log in logs:
            message = json.loads(log['message'])['message']
            if 'Network.requestWillBeSent' in message['method']:
                try:
                    url = message['params']['request']['url']
                except:
                    continue
            
                # Look for specific requests like access tokens or API calls
                if "apigw/history/" in url:
                    # Extract headers or other data from the request
                    
                    self.headers = message['params']['request']['headers']
                    break


    def click_element(self, element):
        try:
            ActionChains(self.driver).move_to_element(element).click(element).perform()
            return True
        except Exception as e:
            try:
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element)).click()
            except:
                return False
    def confirmBet(self):
        keypad_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="keypad-button-3"]'))
        )
        self.click_element(keypad_button)

        place_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="keypad-button-cta"]'))
        )
        self.click_element(place_button)

        confirm_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="betslip-footer-right-button"]'))
        )
        self.click_element(confirm_button)
        try:
            self.click_element(confirm_button)
        except:
            pass

        print('Bet has successfully been placed')

    def placeBet(self, runner_name, target_odd, comp_id):
        self.driver.get(f"https://www.sportsbet.com.au/greyhound-racing/international/-/race-2-{str(comp_id)}")


        if self.add_to_slip(runner_name,target_odd):
            if self.confirmBet():
                print("Bet Placed")
        '''

        if self.mo(runner_name, target_odd):
            self.confirmBet()
            return True

        response = requests.post('http://127.0.0.1:5000/clear_specific_bet', json={'runner_name': runner_name, "target_odd": str(target_odd), "comp_id": comp_id})
        return False
        '''


    def add_to_slip(self, runner_name, target_odd):
        try:
            racecard = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation-id="racecard-body"]'))
            )

            runners = racecard.find_elements(By.CSS_SELECTOR, 'div[data-automation-id^="racecard-outcome-"]')

            for runner in runners:
                try:
                    try:
                        name_element = runner.find_element(By.CSS_SELECTOR, 'div[data-automation-id="racecard-outcome-name"]')
                    except:
                        continue
                    name_text = name_element.text.strip()

                    if name_text.lower() == runner_name.lower():
                        try:
                            odd_elements = runner.find_elements(By.CSS_SELECTOR, 'span[data-automation-id="price-text"]')
                        except:
                            print('Cant find odds elements')
                            return False

                        for odd_element in odd_elements:
                            odd_text = odd_element.text.strip()

                            if odd_text == str(target_odd) or float(target_odd)-float(odd_text) < 2.5:
                                if self.click_element(odd_element):

                                    logs = self.driver.get_log("performance")
        
                                    for log in logs:
                                        message = json.loads(log['message'])['message']
                                        if 'Network.requestWillBeSent' in message['method']:
                                            try:
                                                url = message['params']['request']['url']
                                            except:
                                                continue
                                        
                                            # Look for specific requests like access tokens or API calls
                                            if "https://www.sportsbet.com.au/apigw/acs/bets/combinations" == url:
                                                # Extract headers or other data from the request
                                                
                                                print('Bet added to slip')
                                                return True


                                        

                                print('Error Adding to betslip')
                                return False
                except Exception as e:
                    print(f"An error occurred while processing runner {runner_name}: {e}")
                    continue

            print(f"No match found for {runner_name} with odd {target_odd}")
            return False

        except Exception as e:
            print(f"An error occurred: {e}")


    def enter_price(self):
        try:
            # Find all the keypad buttons once, assuming they are all loaded
            keypad_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[data-automation-id^="keypad-button-"]')

            # Iterate through the PRICE list and click the respective buttons
            for i in PRICE:
                button_to_click = None
                for button in keypad_buttons:
                    if button.get_attribute('data-automation-id') == f'keypad-button-{str(i)}':
                        button_to_click = button
                        break

                if button_to_click:
                    # Click the found button
                    button_to_click.click()
                
                else:
                    print(f"Keypad button ({str(i)}) not found.")
                    return False  # Exit function if a button is not found

            return True  # Return True if all buttons were clicked

        except Exception as e:
            print(f"Error clicking keypad buttons: {e}")
            return False

    def confirmBet(self):
        try:
            # Step 1: Click the keypad button (3)
            self.enter_price()
            # Step 2: Click the place button (CTA button)
            try:
                place_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="keypad-button-cta"]'))
                )
                self.click_element(place_button)
                print("Place button clicked.")
            except Exception as e:
                print(f"Error clicking place button: {e}")
                return False  # Exit function if this step fails

            # Step 3: Click the confirm button (betslip footer button)
            try:
                confirm_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="betslip-footer-right-button"]'))
                )
                self.click_element(confirm_button)
                print("Confirm button clicked.")
            except Exception as e:
                print(f"Error clicking confirm button: {e}")
                return False  # Exit function if this step fails

            # Final Step: Retry clicking confirm button (in case of interference)
            try:
                self.click_element(confirm_button)
                print("Confirm button clicked again to ensure bet placement.")

                logs = self.driver.get_log("performance")
        
                for log in logs:
                    message = json.loads(log['message'])['message']
                    if 'Network.requestWillBeSent' in message['method']:
                        try:
                            url = message['params']['request']['url']
                        except:
                            continue
                    
                        # Look for specific requests like access tokens or API calls
                        if "https://www.sportsbet.com.au/apigw/acs/bets" == url:
                            # Extract headers or other data from the request
                            
                            print('Confirmed Bet')
                            return True
                
                print('Error Confirming Bet')
                return False
            except Exception as e:
                print(f"Error retrying confirm button click: {e}")

            return True  # Return True if everything succeeded

        except Exception as e:
            print(f"An unexpected error occurred in confirmBet: {e}")
            return False  # Return False if an unexpected error occurs

import os
import sys

Bet()
