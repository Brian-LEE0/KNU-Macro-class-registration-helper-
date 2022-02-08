import datetime
from time import sleep
import requests
import winsound as sd
import re

TOKEN = ''
subj_cd = ''
def beepsound():
    fr = 2000    # range : 37 ~ 32767
    du = 3000     # 1000 ms ==1second
    sd.Beep(fr, du) # winsound.Beep(frequency, duration)

def crawling(code) :
	try :
		URL = "http://my.knu.ac.kr/stpo/stpo/cour/lectReqCntEnq/list.action"
		body = {
			'lectReqCntEnq.search_sub_class_cde' : code[7:10],
			'lectReqCntEnq.search_subj_cde' : code[0:7],
			'searchValue' : code
		}
		web = requests.post(URL, data=body)
		data = web.text.split("<tbody>")[1]

		subj_nm = data.split("\"subj_nm\">")[1].split("</td>")[0]
		unit = data.split("\"unit\">")[1].split("</td>")[0]
		pf_nm = data.split("\"prof_nm\">")[1].split("</td>")[0]
		lect_quota = data.split("\"lect_quota\">")[1].split("</td>")[0]
		lect_req_cnt = data.split("\"lect_req_cnt\">")[1].split("</td>")[0]

		return {
		'subj_nm' : subj_nm,
		'subj_cd' : code,
		'unit' : unit,
		'pf_nm' : pf_nm,
		'lect_quota' : int(lect_quota),
		'lect_req_cnt' : int(lect_req_cnt)
		}
	except Exception as ex :
		print(f'ERROR : 올바른 과목코드가 아닙니다 다시 확인해 주세요!')





def req(**sub):
	try :
	    TARGET_URL = 'https://notify-api.line.me/api/notify'
	    # 요청합니다.
	    mes={'message': '\n[중요!]\n' + sub['subj_nm'] + '(' + sub['subj_cd'] + ')' + '\n정원 ' + str(sub['lect_quota'] - sub['lect_req_cnt']) + '명 발생!!\nsugang.knu.ac.kr'}
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
		beepsound()



if __name__ == "__main__":
	std = 0
	try :
		print("#######################################")
		subj_cd = input("과목코드를 입력해 주세요 : ").upper()
		while 1 : 
			if len(subj_cd) != 10 :
				subj_cd = input("올바른 과목코드를 입력해 주세요 : ").upper()
			else :
				break
		TOKEN = input("발급받은 라인 토큰 코드를 입력해 주세요 : ")
		print("#######################################")

	except Exception as ex :
		print(f'ERROR : {ex}')

	while 1 :
		try :
			subj = crawling(subj_cd)
			print(subj)
			if std != subj['lect_quota'] :
				std = subj['lect_quota']
				if subj['lect_quota'] > subj['lect_req_cnt'] :
					for i in range(3) :
						req(**subj)
						sleep(2)
			sleep(5)

		except Exception as ex :
			sleep(5)



