from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import sys, os
import datetime
from time import sleep
import requests

TOKEN = ''
temp = ''
driver = ''

def init() :
	global driver
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
	chrome_options.add_argument("headless")
	driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=chrome_options)
	

def countdown(t):
	try :
		while t:
			mins, secs = divmod(t, 60)
			timer = '{:02d}:{:02d}'.format(mins, secs)
			print(timer, end="\r")
			sleep(1)
			t -= 1
	except KeyboardInterrupt as kI:
		print(f'ERROR : {kI}')
		exit()
	except Exception as ex:
		print(f'ERROR : {ex}')

def crawling(subjcd,idx) :
	global driver
	try :
		driver.set_window_size(3000, 2000)
		driver.get('https://knuin.knu.ac.kr/public/stddm/lectPlnInqr.knu')
		driver.implicitly_wait(0.1)
		driver.find_element(By.XPATH,'//*[@id="schCode"]/option[4]').click()
		driver.implicitly_wait(0.1)
		driver.find_element(By.XPATH,'//*[@id="schCodeContents"]').send_keys(subjcd)
		driver.implicitly_wait(0.1)
		driver.find_element(By.XPATH,'//*[@id="btnSearch"]').click()
		driver.implicitly_wait(3)
		subj_cd = driver.find_element(By.XPATH,'//*[@id="grid01_cell_'+ str(idx-1)+'_6"]/nobr').text
		subj_name = driver.find_element(By.XPATH,'//*[@id="grid01_cell_'+ str(idx-1)+'_7"]/nobr').text
		subj_limit = driver.find_element(By.XPATH,'//*[@id="grid01_cell_'+ str(idx-1)+'_16"]/nobr').text
		subj_current = driver.find_element(By.XPATH,'//*[@id="grid01_cell_'+ str(idx-1)+'_17"]/nobr').text
		
		return {
		'subj_name' : subj_name,
		'subj_cd' : subj_cd,
		'subj_limit' : int(subj_limit),
		'subj_current' : int(subj_current)
		}
	except Exception as ex :
		print(f'ERROR : 올바른 과목코드가 아닙니다 다시 확인해 주세요!')


def init_req(**sub):
	try :
	    TARGET_URL = 'https://notify-api.line.me/api/notify'
	    # 요청합니다.
	    mes={'message': sub['subj_name'] +'('+ sub['subj_cd'] +')'+'과목의 정원변경 추적을 시작합니다.'}
	    response = requests.post(
	    TARGET_URL,
	    headers={
	    'Authorization': 'Bearer ' + TOKEN
	    },
	    data=mes
	    )
	    print(mes['message'])
	except :
		print(f'ERROR : 올바른 토큰이 아닙니다!')

def req(**sub):
	try :
	    TARGET_URL = 'https://notify-api.line.me/api/notify'
	    # 요청합니다.
	    mes={'message': '\n[중요!]\n' + sub['subj_name'] + '(' + sub['subj_cd'] + ')' + '\n정원 ' + str(sub['subj_limit'] - sub['subj_current']) + '명 발생!!\nsugang.knu.ac.kr'}
	    response = requests.post(
	    TARGET_URL,
	    headers={
	    'Authorization': 'Bearer ' + TOKEN
	    },
	    data=mes
	    )
	    print(mes['message'])
	except :
		print(f'ERROR : 올바른 토큰이 아닙니다!')

if __name__ == "__main__":
	std = 0
	init()
	try :
		print("#######################################")
		subj_cd = input("담당교수님 성함을 입력해 주세요 (ex : 하이랜드) : ")
		subj_idx = int(input("해당하는 교과목의 인덱스를 알려주세요 (ex : 7) : "))
		TOKEN = input("발급받은 라인 토큰 코드를 입력해 주세요 : ")
		print("#######################################")

	except Exception as ex :
		print(f'ERROR : {ex}')

	subj = crawling(subj_cd,subj_idx)
	init_req(**subj)

	while 1 :
		try :
			subj = crawling(subj_cd,subj_idx)
			print(subj)
			if std != subj['subj_current'] :
				std = subj['subj_current']
				if subj['subj_limit'] > subj['subj_current'] :
					for i in range(3) :
						req(**subj)
						countdown(2)
			countdown(5)

		except Exception as ex :
			driver.close()
			print('드라이버 재실행 중')
			init()
			countdown(5)


