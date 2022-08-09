import sys, os
import datetime
from time import sleep
import requests
from requests.structures import CaseInsensitiveDict
import json

TOKEN = ''
temp = ''
index = 0

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


def req_info_subjcode(year,semester_cd,subj_cd) :
	url = "https://knuin.knu.ac.kr/public/web/stddm/lsspr/syllabus/lectPlnInqr/selectListLectPlnInqr"

	headers = CaseInsensitiveDict()
	headers["Content-Type"] = "application/json"
	
	data = {
		"search":
		{"estblYear":"",
		"estblSmstrSctcd":"",
		"sbjetCd":"",
		"sbjetNm":"",
		"crgePrfssNm":"",
		"sbjetRelmCd":"",
		"sbjetSctcd":"",
		"estblDprtnCd":"",
		"rmtCrseYn":"",
		"rprsnLctreLnggeSctcd":"",
		"flplnCrseYn":"",
		"pstinNtnnvRmtCrseYn":"",
		"dgGbDstrcRmtCrseYn":"",
		"sugrdEvltnYn":"",
		"gubun":"01",
		"isApi":"Y",
		"bldngSn":"",
		"bldngCd":"",
		"bldngNm":"",
		"lssnsLcttmUntcd":"",
		"sbjetSctcd2":"",
		"contents":"",
		"lctreLnggeSctcd":"ko"}
	}
	data["search"]["estblYear"] = year
	data["search"]["estblSmstrSctcd"] = semester_cd
	data["search"]["sbjetCd"] = subj_cd[0:8]
	data["search"]["contents"] = subj_cd[0:8]
	resp = requests.post(url, headers=headers, data=json.dumps(data))
	return json.loads(resp.text)

def init_crawling(year,semester_cd,subj_cd):
	try :
		global index
		subj_info = (req_info_subjcode(year,semester_cd,subj_cd))["data"]

		for data in subj_info :
			if(data["crseNo"] == subj_cd) :
				return data[index]
			else :
				index+=1
		return -1
	except Exception as ex :
		return -1



def crawling(year,semester_cd,subj_cd) :
	try :
		subj_info = (req_info_subjcode(year,semester_cd,subj_cd))["data"][index]

		return {
			'subj_name' : subj_info["sbjetNm"],
			'subj_cd' : subj_info["crseNo"],
			'subj_limit' : int(subj_info["attlcPrscpCnt"]),
			'subj_current' : int(subj_info["appcrCnt"])
		}
		
	except Exception as ex :
		return -1

		


def init_req(sub):
	try :
	    TARGET_URL = 'https://notify-api.line.me/api/notify'
	    # 요청합니다.
	    mes={'message': sub['sbjetNm'] +'('+ sub['crseNo'] +')'+'과목의 정원변경 추적을 시작합니다.'}
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

def req(sub):
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
	std = -1
	print("현재 사용하시는 프로그램은 최종 판으로, 학교 사이트가 다시 개편되기 전에는 계속 사용하실 수 있습니다")
	print("이 프로그램은 전자공학부 2016학번 이 아무개가 만든 프로그램입니다. 자유롭게 사용하셔도 됩니다^^")
	try :
		print("#######################################")
		year = input("년도를 입력해주세요 (ex : 2022) : ")
		semester = int(input("학기를 입력해 주세요 (1학기는 1, 2학기는 2, 여름계절은 3, 겨울계절은 4) : "))
		subj_cd = input("과목코드를 입력해 주세요 (ex : CLTR0023-001) : ").upper()
		while 1 : 
			if len(subj_cd) != 12 :
				subj_cd = input("올바른 과목코드를 입력해 주세요 : ").upper()
			else :
				break
		TOKEN = input("발급받은 라인 토큰 코드를 입력해 주세요 : ")
		print("#######################################")

	except Exception as ex :
		print(f'ERROR : {ex}')

	if(semester == 1):
		semester_cd = "CMBS001400001"
	elif(semester == 2):
		semester_cd = "CMBS001400002"
	elif(semester == 3):
		semester_cd = "CMBS001400004"
	elif(semester == 4):
		semester_cd = "CMBS001400003"

	subj = crawling(year,semester_cd,subj_cd)
	if(subj == -1) :
		print(f'ERROR : 올바른 과목코드가 아닙니다 다시 확인해 주세요!')
		countdown(5)
		exit(0)

	init_req(subj)

	while 1 :
		try : 
			subj = crawling(year,semester_cd,subj_cd)
			print(subj)
			if std != subj['subj_current'] :
				std = subj['subj_current']
				if subj['subj_limit'] > subj['subj_current'] :
					for i in range(3) :
						req(**subj)
						countdown(2)
			countdown(5)
		except Exception as ex :
			countdown(5)

	


