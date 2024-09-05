import requests
import time
import subprocess
import sys

# Command to run the other Python file
#https://raw.githubusercontent.com/bevan654/bevangaming/main/version.txt


CURRENT_VERSION = '0.0.2'



class Main:
    def __init__(self):
        self.check_for_updates()



    def LOG(self,text,color='white'):
        print(text)


    def download_update(self,new_version):
        while True:
            try:
                response = requests.get('https://raw.githubusercontent.com/bevan654/bevangaming/main/main.py')
            except:
                self.LOG("[DOWNLOAD_UPDATE] Request Error",'red')
                time.sleep(1)
                continue

            if response.status_code == 200:
                new_version= new_version.decode('utf-8').strip()
                with open(f'bot/{new_version}.py','wb') as e:
                    e.write(response.content)

                subprocess.run(["start", "cmd", "/k", f"python bot/{new_version}.py"], shell=True)

                sys.exit()


                self.LOG('Download Finished')
                return True
            else:
                self.LOG('[CHECK_FOR_UPDATES] Bad Response Status')

    def check_for_updates(self):
        self.LOG("Checking for updates",'yellow')
        while True:
            try:
                response = requests.get('https://raw.githubusercontent.com/bevan654/bevangaming/main/version.txt')
            except:
                self.LOG("[CHECK_FOR_UPDATES] Request Error",'red')
                time.sleep(1)
                continue

            if response.status_code == 200:
                response = response.content.strip().lower()
                if CURRENT_VERSION != response:
                    self.LOG('[CHECK_FOR_UPDATES] New updates available!')
                    self.download_update(response)

                    break
                time.sleep(1)


            else:
                self.LOG("[CHECK_FOR_UPDATES] Bad Response Status")



Main()
