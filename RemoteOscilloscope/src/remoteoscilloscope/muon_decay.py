# --------------------------------------------------
# 上からPMTをABCとすると
# Ch1: ミューオン、電子の生信号(B)
# Ch2: A & B & bar(C)の論理積
# --------------------------------------------------
import pyvisa
from dotenv import load_dotenv
import os
from time import sleep
from muon_decay_lib import * # WARNINGは無視

# --------- 初期設定 ---------
TIME_GRID_LENGTH = 4 # us
CH1_SCALE = 7 # mV
CH2_SCALE = 100 # mV
CH1_TRIGGER_LEVEL = -10 # mV
CH2_TRIGGER_LEVEL = -100 # mV
DELAY_TIME = 50 # ns
RESET_TIMEOUT = 36 # us

MAX_COUNT = 2 # 崩壊の測定回数
# ---------------------------

load_dotenv()

IP_ADDRESS = os.getenv('IP_ADDRESS')
ipaddr = f'TCPIP::{IP_ADDRESS}::INSTR'
rm = pyvisa.ResourceManager('@py')
scope = rm.open_resource(ipaddr)

scope.timeout = 10000 # エラーが出るまでのタイムアウトを10000msに設定

init_command = [
    # 初期化
    "*RST",

    # Ch2の追加
    "DISplay:WAVEView1:CH2:STATE ON",

    # レジスタンスの設定
    "CH1:TERmination 50", # 50Ω
    "CH2:TERmination 50",

    # HORIZONTALの設定
    f"HORizontal:SCAle {TIME_GRID_LENGTH}e-6", # 横軸のスケールを設定
    "HORizontal:POSition 90", # 90%ずらす

    # VERTICALの設定
    f"CH1:SCAle {CH1_SCALE}e-3", # 縦軸のスケールを設定
    f"CH2:SCAle {CH2_SCALE}e-3",
    "CH1:POSition 4.0", # 4 grid分ずらす
    "CH2:POSition 4.0",

    # TRIGGERの設定
    "TRIGger:B:STATE ON", # 2つ目のトリガーを有効にする
    "TRIGger:A:EDGE:SLOpe FALL", # トリガーの経ち下がりでトリガー
    "TRIGger:B:EDGE:SLOpe FALL",
    "TRIGger:A:EDGE:SOUrce CH2", # 2つ目のトリガーのソースをCH2に設定
    f"TRIGger:B:LEVel:CH1 {CH1_TRIGGER_LEVEL}e-3", # トリガーレベルを設定
    f"TRIGger:A:LEVel:CH2 {CH2_TRIGGER_LEVEL}e-3",
    f"TRIGger:B:TIMe {DELAY_TIME}e-9", # トリガーの時間を設定
    "TRIGger:B:RESET:TYPe TIMEOut", # TIMEOUTの設定
    f"TRIGger:B:RESET:TIMEOut:TIMe {RESET_TIMEOUT}e-6", # TIMEOUTの時間を設定
]

config_command = [
    "DATa:ENCdg ASCIi", # データのエンコードをASCIIに設定
    "DATa:SOUrce CH1", # データのソースをCH1に設定
    # "DATa:STARt?", # データの開始位置 デフォルトで1
    # 'DATa:STOP?',  # データの終了位置 1shot分のpt数
    # 'HORizontal:RECOrdlength?',  # データのpt数(DATa:STOP?と一致するか確認)
]

# オシロスコープの状態
ACQuire_STATE = {
    "STOP": "0\n",
    "RUN": "1\n",
}

run_command(scope, init_command)
sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)
run_command(scope, config_command)
sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)    
filename = get_filename()
make_csv(filename)

def get_waveform(scope: pyvisa.resources.MessageBasedResource):
    scope.write("ACQuire:STATE ON")
    scope.write("ACQuire:STOPAfter SEQuence") # single/seq mode"
    counter = Counter()
    while True:
        state = scope.query("ACQuire:STATE?")
        if state == ACQuire_STATE["STOP"]:
            print("hit!!!!!")
            t, v_ch1 = SAVe_DATa_SOUrce(1, scope)
            _, v_ch2 = SAVe_DATa_SOUrce(2, scope)
            write_csv((t, v_ch1, v_ch2), filename)
            break
        counter.print()
        sleep(2)

for i in range(MAX_COUNT):
    try:
        print(f"{i+1}回目の計測")
        get_waveform(scope)
    
    except KeyboardInterrupt:
        print("コマンドを停止しました。")
        break

scope.close()
rm.close()

