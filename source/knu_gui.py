import json
from time import sleep
import requests
import re
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import datetime
import os

class KNUMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KNU 수강신청 매크로")
        # 창 크기를 충분히 크게 설정하고 크기 고정
        self.root.geometry("600x600")
        self.root.minsize(600, 600)
        self.root.maxsize(600, 600)
        self.root.resizable(False, False)
        
        # 설정 파일 경로
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knu_settings.json")
        
        # 학기 정보 설정
        self.semester_options = [
            ("1학기", "CMBS001400001"),
            ("2학기", "CMBS001400002"),
            ("계절학기(동계)", "CMBS001400003"),
            ("계절학기(하계)", "CMBS001400004")
        ]
        
        # 변수 초기화
        self.BOT_TOKEN = ""
        self.CHAT_ID = ""
        self.subj_cd = ""
        self.year = str(datetime.datetime.now().year)
        self.semester_code = "CMBS001400001"  # 기본값: 1학기
        self.std = 0
        self.running = False
        self.thread = None
        
        # UI 구성 요소 생성
        self.create_widgets()
        
        # 저장된 설정 불러오기
        self.load_settings()
        
        # 프로그램 종료 시 설정 저장
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        # 프레임 생성
        input_frame = ttk.LabelFrame(self.root, text="입력 설정")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # 년도 및 학기 선택 프레임
        year_semester_frame = ttk.Frame(input_frame)
        year_semester_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(year_semester_frame, text="개설년도:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.year_entry = ttk.Entry(year_semester_frame, width=6)
        self.year_entry.insert(0, self.year)
        self.year_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(year_semester_frame, text="개설학기:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.semester_var = tk.StringVar(value="1학기")
        self.semester_combobox = ttk.Combobox(year_semester_frame, 
                                            textvariable=self.semester_var,
                                            values=[option[0] for option in self.semester_options],
                                            state="readonly",
                                            width=12)
        self.semester_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.semester_combobox.bind("<<ComboboxSelected>>", self.on_semester_change)
        
        # 과목코드 입력
        ttk.Label(input_frame, text="과목코드 ex)CLTR0024-001:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.subj_cd_entry = ttk.Entry(input_frame, width=20)
        self.subj_cd_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 텔레그램 봇 토큰 입력
        ttk.Label(input_frame, text="텔레그램 봇 토큰:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.bot_token_entry = ttk.Entry(input_frame, width=50)
        self.bot_token_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 상태 표시 프레임
        status_frame = ttk.LabelFrame(self.root, text="현재 상태")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="준비 완료")
        ttk.Label(status_frame, textvariable=self.status_var).pack(padx=5, pady=5, anchor="w")
        
        # 강의 정보 표시
        self.info_frame = ttk.Frame(status_frame)
        self.info_frame.pack(fill="x", padx=5, pady=5)
        
        self.subj_info_var = tk.StringVar(value="강의 정보: 검색 전")
        ttk.Label(self.info_frame, textvariable=self.subj_info_var).pack(anchor="w")
        
        self.quota_info_var = tk.StringVar(value="수강 정원: 검색 전")
        ttk.Label(self.info_frame, textvariable=self.quota_info_var).pack(anchor="w")
        
        # 로그 창
        log_frame = ttk.LabelFrame(self.root, text="로그")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 우클릭 메뉴 추가
        self.create_text_context_menu()
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="크롤링 시작", command=self.start_crawling)
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="중지", command=self.stop_crawling, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        self.test_button = ttk.Button(button_frame, text="텔레그램 테스트", command=self.test_telegram)
        self.test_button.pack(side="left", padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="로그 지우기", command=self.clear_log)
        self.clear_button.pack(side="right", padx=5)
    
    def on_semester_change(self, event):
        """학기 선택이 변경되었을 때 호출됩니다."""
        selected_name = self.semester_var.get()
        for name, code in self.semester_options:
            if name == selected_name:
                self.semester_code = code
                self.log(f"개설학기를 '{name}'({code})로 변경했습니다.")
                break
    
    def create_text_context_menu(self):
        """로그 텍스트에 우클릭 컨텍스트 메뉴를 추가합니다."""
        self.text_menu = tk.Menu(self.root, tearoff=0)
        self.text_menu.add_command(label="복사", command=self.copy_text)
        self.text_menu.add_command(label="붙여넣기", command=self.paste_text)
        self.text_menu.add_command(label="잘라내기", command=self.cut_text)
        self.text_menu.add_separator()
        self.text_menu.add_command(label="모두 선택", command=self.select_all_text)
        
        # 마우스 우클릭 이벤트에 메뉴 표시 함수를 바인딩
        self.log_text.bind("<Button-3>", self.show_text_menu)
        
        # 사용자 입력 필드에도 적용
        self.subj_cd_entry.bind("<Button-3>", self.show_entry_menu)
        self.bot_token_entry.bind("<Button-3>", self.show_entry_menu)
        self.year_entry.bind("<Button-3>", self.show_entry_menu)

    def show_text_menu(self, event):
        """마우스 우클릭 위치에 컨텍스트 메뉴를 표시합니다."""
        self.text_menu.post(event.x_root, event.y_root)
    
    def show_entry_menu(self, event):
        """입력 필드에서 우클릭 시 컨텍스트 메뉴를 표시합니다."""
        self.text_menu.post(event.x_root, event.y_root)

    def copy_text(self):
        """선택한 텍스트를 클립보드에 복사합니다."""
        try:
            widget = self.root.focus_get()
            widget.event_generate("<<Copy>>")
        except:
            pass

    def paste_text(self):
        """클립보드의 텍스트를 붙여넣습니다."""
        try:
            widget = self.root.focus_get()
            widget.event_generate("<<Paste>>")
        except:
            pass

    def cut_text(self):
        """선택한 텍스트를 잘라냅니다."""
        try:
            widget = self.root.focus_get()
            widget.event_generate("<<Cut>>")
        except:
            pass

    def select_all_text(self):
        """텍스트를 모두 선택합니다."""
        try:
            widget = self.root.focus_get()
            if isinstance(widget, tk.Text):
                widget.tag_add(tk.SEL, "1.0", tk.END)
                widget.mark_set(tk.INSERT, "1.0")
                widget.see(tk.INSERT)
            elif isinstance(widget, tk.Entry):
                widget.select_range(0, tk.END)
        except:
            pass
    
    def load_settings(self):
        """저장된 설정을 불러옵니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    # 저장된 설정 있으면 입력 필드에 설정
                    if 'bot_token' in settings:
                        self.bot_token_entry.delete(0, tk.END)
                        self.bot_token_entry.insert(0, settings['bot_token'])
                        self.BOT_TOKEN = settings['bot_token']
                    
                    if 'subj_cd' in settings:
                        self.subj_cd_entry.delete(0, tk.END)
                        self.subj_cd_entry.insert(0, settings['subj_cd'])
                        self.subj_cd = settings['subj_cd']
                    
                    if 'year' in settings:
                        self.year_entry.delete(0, tk.END)
                        self.year_entry.insert(0, settings['year'])
                        self.year = settings['year']
                    
                    if 'semester_code' in settings:
                        self.semester_code = settings['semester_code']
                        for name, code in self.semester_options:
                            if code == self.semester_code:
                                self.semester_var.set(name)
                                break
                
                self.log("이전 설정을 불러왔습니다.")
        except Exception as e:
            self.log(f"설정 파일 로드 중 오류 발생: {e}")
    
    def save_settings(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            settings = {
                'bot_token': self.bot_token_entry.get(),
                'subj_cd': self.subj_cd_entry.get().upper(),
                'year': self.year_entry.get(),
                'semester_code': self.semester_code
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            self.log("현재 설정이 저장되었습니다.")
        except Exception as e:
            self.log(f"설정 저장 중 오류 발생: {e}")
    
    def on_closing(self):
        """프로그램 종료 시 호출되는 함수입니다."""
        # 크롤링 중이면 중지
        if self.running:
            self.stop_crawling()
        
        # 설정 저장
        self.save_settings()
        
        # 프로그램 종료
        self.root.destroy()
    
    def log(self, message):
        """로그 메시지를 로그 창에 추가합니다."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)  # 스크롤을 맨 아래로 이동
    
    def clear_log(self):
        """로그 창의 내용을 지웁니다."""
        self.log_text.delete(1.0, tk.END)
    
    def start_crawling(self):
        """크롤링을 시작합니다."""
        self.subj_cd = self.subj_cd_entry.get().upper()
        self.BOT_TOKEN = self.bot_token_entry.get()
        self.year = self.year_entry.get()
        
        # 입력값 검증
        if not self.subj_cd:
            messagebox.showerror("오류", "과목코드를 입력해 주세요")
            return
        
        if not self.BOT_TOKEN:
            messagebox.showerror("오류", "텔레그램 봇 토큰을 입력해 주세요")
            return
        
        if not self.year.isdigit() or len(self.year) != 4:
            messagebox.showerror("오류", "개설년도를 올바르게 입력해 주세요 (4자리 숫자)")
            return
        
        # 현재 설정 저장
        self.save_settings()
        
        # 채팅 ID 가져오기
        self.log("텔레그램 채팅 ID를 가져오는 중...")
        try:
            self.CHAT_ID = self.get_chat_id(self.BOT_TOKEN)
            self.log(f"채팅 ID 가져오기 성공: {self.CHAT_ID}")
        except Exception as e:
            self.log(f"채팅 ID 가져오기 실패: {e}")
            messagebox.showerror("오류", f"채팅 ID 가져오기 실패: {e}\n봇에 먼저 메시지를 보냈는지 확인하세요.")
            return
        
        # UI 상태 업데이트
        self.status_var.set("크롤링 중...")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.subj_cd_entry.config(state="disabled")
        self.bot_token_entry.config(state="disabled")
        self.year_entry.config(state="disabled")
        self.semester_combobox.config(state="disabled")
        
        # 크롤링 스레드 시작
        self.running = True
        self.thread = threading.Thread(target=self.crawling_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_crawling(self):
        """크롤링을 중지합니다."""
        self.running = False
        self.status_var.set("중지됨")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.subj_cd_entry.config(state="normal")
        self.bot_token_entry.config(state="normal")
        self.year_entry.config(state="normal")
        self.semester_combobox.config(state="readonly")
        self.log("크롤링이 중지되었습니다.")
    
    def test_telegram(self):
        """텔레그램 봇 연결을 테스트합니다."""
        self.BOT_TOKEN = self.bot_token_entry.get()
        
        if not self.BOT_TOKEN:
            messagebox.showerror("오류", "텔레그램 봇 토큰을 입력해 주세요")
            return
        
        try:
            # 채팅 ID 가져오기
            self.CHAT_ID = self.get_chat_id(self.BOT_TOKEN)
            
            # 테스트 메시지 전송
            message = "테스트 메시지입니다. KNU 수강신청 매크로가 정상적으로 작동 중입니다."
            url = f'https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage'
            data = {
                'chat_id': self.CHAT_ID,
                'text': message
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.log("텔레그램 테스트 메시지 전송 성공")
                messagebox.showinfo("성공", "텔레그램 테스트 메시지 전송 성공")
                self.save_settings()
                
            else:
                self.log(f"텔레그램 테스트 메시지 전송 실패: {response.text}")
                messagebox.showerror("오류", f"텔레그램 테스트 메시지 전송 실패: {response.text}")
        
        except Exception as e:
            self.log(f"텔레그램 테스트 실패: {e}")
            messagebox.showerror("오류", f"텔레그램 테스트 실패: {e}")
    
    def crawling_thread(self):
        """백그라운드에서 크롤링을 수행하는 스레드 함수입니다."""
        while self.running:
            try:
                subj = self.crawling(self.subj_cd, self.year, self.semester_code)
                if subj:
                    # UI 업데이트를 메인 스레드에서 실행
                    self.root.after(0, self.update_ui_with_subject, subj)
                    
                    if self.std != subj['appcrCnt']:
                        prev_count = self.std
                        self.std = subj['appcrCnt']
                        
                        # 신청 인원이 변경되었고, 여석이 있는 경우
                        if subj['attlcPrscpCnt'] > subj['appcrCnt']:
                            self.root.after(0, self.log, f"빈 자리 발생! 정원: {subj['attlcPrscpCnt']}, 신청: {subj['appcrCnt']}, 여석: {subj['attlcPrscpCnt'] - subj['appcrCnt']}명")
                            
                            # 신청 인원이 감소한 경우만 알림 (취소가 발생했을 때)
                            if self.std < prev_count or prev_count == 0:
                                for i in range(3):
                                    if not self.running:
                                        break
                                    self.req(**subj)
                                    self.countdown_ui(2)
                        else:
                            self.root.after(0, self.log, f"정원이 찼습니다. 정원: {subj['attlcPrscpCnt']}, 신청: {subj['appcrCnt']}")
                    else:
                        self.root.after(0, self.log, f"변화 없음. 정원: {subj['attlcPrscpCnt']}, 신청: {subj['appcrCnt']}")
                
                # 5초 대기
                self.countdown_ui(5)
            
            except Exception as e:
                self.root.after(0, self.log, f"ERROR: {e}")
                self.countdown_ui(5)
    
    def update_ui_with_subject(self, subj):
        """과목 정보로 UI를 업데이트합니다."""
        self.subj_info_var.set(f"강의 정보: {subj['sbjetNm']} ({subj['crseNo']}) - {subj['totalPrfssNm']} 교수님")
        self.quota_info_var.set(f"수강 정원: {subj['attlcPrscpCnt']}명 중 {subj['appcrCnt']}명 신청 (여석: {subj['attlcPrscpCnt'] - subj['appcrCnt']}명)")
    
    def countdown_ui(self, t):
        """UI 업데이트를 차단하지 않고 카운트다운합니다."""
        for i in range(t):
            if not self.running:
                break
            sleep(1)
    
    def get_chat_id(self, token):
        """텔레그램 봇의 getUpdates API를 호출하여 가장 최근 채팅 ID를 가져옵니다."""
        url = f'https://api.telegram.org/bot{token}/getUpdates'
        response = requests.get(url)
        updates = response.json()
        
        if updates['ok'] and updates['result']:
            # 가장 최근 업데이트에서 chat_id 가져오기
            latest_update = updates['result'][-1]
            chat_id = latest_update['message']['chat']['id']
            return str(chat_id)
        else:
            raise Exception("채팅 ID를 가져올 수 없습니다. 봇에게 먼저 메시지를 보내주세요.")
    
    def req(self, **sub):
        """텔레그램으로 알림을 보냅니다."""
        try:
            message = '\n[중요!]\n' + sub['sbjetNm'] + '(' + sub['crseNo'] + ')' + '\n정원 ' + str(sub['attlcPrscpCnt'] - sub['appcrCnt']) + '명 발생!!\nsugang.knu.ac.kr'
            
            url = f'https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage'
            data = {
                'chat_id': self.CHAT_ID,
                'text': message
            }
            
            response = requests.post(url, data=data)
            self.root.after(0, self.log, f"텔레그램 알림 전송 완료: {message}")
        except Exception as e:
            self.root.after(0, self.log, f"ERROR: 텔레그램 메시지 전송 실패! {e}")
    
    def crawling(self, code, year, semester_code):
        """새로운 API를 사용하여 과목 정보를 크롤링합니다."""
        try:
            self.root.after(0, self.log, f"크롤링 시작: 과목코드={code}, 연도={year}, 학기={semester_code}")
            
            # API 엔드포인트
            url = "https://knuin.knu.ac.kr/public/web/stddm/lsspr/syllabus/lectPlnInqr/selectListLectPlnInqr"
            
            # 요청 헤더
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Origin': 'https://knuin.knu.ac.kr',
                'Referer': 'https://knuin.knu.ac.kr/public/stddm/lectPlnInqr.knu',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'isAjax': 'true'
            }
            
            # 과목 코드가 'XXXX-YYY' 형식인지 확인 (분반이 포함된 경우)
            if '-' in code:
                sbjet_cd, sbjet_dvnno = code.split('-')
            else:
                sbjet_cd = code
                sbjet_dvnno = None
            
            data = {
                "search": {
                    "estblYear": year,
                    "estblSmstrSctcd": semester_code,
                    "sbjetCd": sbjet_cd,
                    "sbjetNm": "",
                    "crgePrfssNm": "",
                    "sbjetRelmCd": "",
                    "sbjetSctcd": "",
                    "estblDprtnCd": "",
                    "rmtCrseYn": "",
                    "rprsnLctreLnggeSctcd": "",
                    "flplnCrseYn": "",
                    "pstinNtnnvRmtCrseYn": "",
                    "dgGbDstrcRmtCrseYn": "",
                    "sugrdEvltnYn": "",
                    "prctsExrmnYn": "",
                    "gubun": "01",
                    "isApi": "Y",
                    "contents": sbjet_cd,
                    "lctreLnggeSctcd": "ko",
                }
            }
            
            # API 호출
            response = requests.post(url, headers=headers, json=data)
            
            # 응답 확인
            if response.status_code == 200:
                result = response.json()
                
                if result["success"] and result["data"] and len(result["data"]) > 0:
                    # 정확히 일치하는 crseNo 찾기
                    for subject_data in result["data"]:
                        # 분반이 지정된 경우 정확히 일치하는 과목만 찾고, 
                        # 그렇지 않으면 과목 코드만 일치하면 첫 번째 결과 반환
                        if (sbjet_dvnno and subject_data['crseNo'] == code) or \
                            (not sbjet_dvnno and subject_data['sbjetCd'] == sbjet_cd):
                            
                            self.root.after(0, self.log, f"과목 정보 찾음: {subject_data['sbjetNm']} ({subject_data['crseNo']})")
                            
                            # 과목 상세 정보 추출하여 반환
                            return {
                                'sbjetNm': subject_data['sbjetNm'],                # 과목명
                                'crseNo': subject_data['crseNo'],                  # 과목번호 (코드-분반)
                                'sbjetCd': subject_data['sbjetCd'],                # 과목코드
                                'sbjetDvnno': subject_data['sbjetDvnno'],          # 분반
                                'crdit': subject_data['crdit'],                    # 학점
                                'totalPrfssNm': subject_data['totalPrfssNm'],      # 교수명
                                'attlcPrscpCnt': int(subject_data['attlcPrscpCnt']), # 수강정원
                                'appcrCnt': int(subject_data['appcrCnt']),         # 신청인원
                                'lssnsTimeInfo': subject_data['lssnsTimeInfo'],    # 강의시간
                                'lctrmInfo': subject_data['lctrmInfo']             # 강의실 정보
                            }
                    
                    self.root.after(0, self.log, f"과목 코드({code})에 대한 정보가 없습니다.")
                else:
                    # 더 이상 결과가 없음
                    self.root.after(0, self.log, f"과목을 찾을 수 없습니다: {code}")
                return None
            else:
                self.root.after(0, self.log, f"API 요청 실패: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            self.root.after(0, self.log, f"크롤링 중 오류 발생: {e}")
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = KNUMacroApp(root)
    root.mainloop()