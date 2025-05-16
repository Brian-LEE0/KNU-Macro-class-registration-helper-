import json
from time import sleep
import requests
import re

BOT_TOKEN = ''
CHAT_ID = ''
subj_cd = ''

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

def crawling(code) :
	try :
		URL = "http://my.knu.ac.kr/stpo/stpo/cour/lectReqCntEnq/list.action"
		body = {
			'lectReqCntEnq.search_sub_class_cde' : code[9:12],
			'lectReqCntEnq.search_subj_cde' : code[0:8],
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

def get_chat_id(token):
    """텔레그램 봇의 getUpdates API를 호출하여 가장 최근 채팅 ID를 가져옵니다."""
    try:
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        response = requests.get(url)
        updates = response.json()
        
        if updates['ok'] and updates['result']:
            # 가장 최근 업데이트에서 chat_id 가져오기
            latest_update = updates['result'][-1]
            chat_id = latest_update['message']['chat']['id']
            print(f"채팅 ID를 성공적으로 가져왔습니다: {chat_id}")
            return str(chat_id)
        else:
            print("채팅 ID를 가져올 수 없습니다. 봇에게 먼저 메시지를 보내주세요.")
            print("텔레그램에서 봇을 찾아 아무 메시지나 보낸 후 프로그램을 다시 실행해주세요.")
            exit()
    except Exception as e:
        print(f"ERROR: 채팅 ID 가져오기 실패! {e}")
        exit()

def req(**sub):
    try:
        message = '\n[중요!]\n' + sub['subj_nm'] + '(' + sub['subj_cd'] + ')' + '\n정원 ' + str(sub['lect_quota'] - sub['lect_req_cnt']) + '명 발생!!\nsugang.knu.ac.kr'
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': CHAT_ID,
            'text': message
        }
        
        response = requests.post(url, data=data)
        print(response)
    except Exception as e:
        print(f'ERROR: 텔레그램 메시지 전송 실패! {e}')


if __name__ == "__main__":
    std = 0
    try:
        print("#######################################")
        subj_cd = input("과목코드를 입력해 주세요 : ").upper()
        while 1: 
            if len(subj_cd) != 12:
                subj_cd = input("올바른 과목코드를 입력해 주세요 : ").upper()
            else:
                break
        
        BOT_TOKEN = input("텔레그램 봇 토큰을 입력해 주세요 : ")
        print("채팅 ID를 가져오는 중... (봇에 메시지를 먼저 보냈는지 확인해주세요)")
        CHAT_ID = get_chat_id(BOT_TOKEN)
        print("#######################################")

    except Exception as ex:
        print(f'ERROR : {ex}')

    while 1:
        try:
            subj = crawling(subj_cd)
            print(subj)
            if std != subj['lect_req_cnt']:
                std = subj['lect_req_cnt']
                if subj['lect_quota'] > subj['lect_req_cnt']:
                    for i in range(3):
                        req(**subj)
                        countdown(2)
            
            countdown(5)
            

        except Exception as ex:
            print(f'ERROR : {ex}')
            countdown(5)



