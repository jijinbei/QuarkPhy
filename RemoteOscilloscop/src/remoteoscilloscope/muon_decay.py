# --------------------------------------------------
# 上からPMTをABCとすると
# Ch1: ミューオン、電子の生信号(B)
# Ch2: A & B & bar(C)の論理積
# --------------------------------------------------
import numpy as np
import pyvisa
import csv
from dotenv import load_dotenv
import os
from time import sleep
from lib import Converter, Counter, run_command # WARNINGは無視

# --------- 初期設定 ---------
TIME_GRID_LENGTH = 4 # us
CH1_SCALE = 6 # mV
CH2_SCALE = 100 # mV
CH1_TRIGGER_LEVEL = -10 # mV
CH2_TRIGGER_LEVEL = -100 # mV
DELAY_TIME = 50 # ns
RESET_TIMEOUT = 36 # us
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
    
    # ACQUIREの設定
    "ACQuire:STOPAfter SEQuence" # single/seq mode
]

config_command = [
    # 'data:encdg SRIBINARY', # signed integer
    # 'data:source CH1',
    # "DATa:STARt?", # データの開始位置 デフォルトで1
    # 'DATa:STOP?',  # データの終了位置 1shot分のpt数
    # 'HORizontal:RECOrdlength?',  # データのpt数(DATa:STOP?と一致するか確認)
    'wfmoutpre:byt_n 1',  # 1 byte per sample
    "SAVE:WAVEform:FORMat CSV",
]

run_command(scope, init_command)

sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)

run_command(scope, config_command)


# オシロスコープの状態
ACQuire_STATE = {
    "STOP": "0\n",
    "RUN": "1\n",
}

sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)

# converter = Converter(scope) #(TODO: 未実装)
# converter.
counter = Counter()

while True:
    state = scope.query("ACQuire:STATE?")
    if state == ACQuire_STATE["STOP"]:
        bin_wave = scope.query_binary_values("CURVe?", datatype='d', is_big_endian=True, container=np.array, chunk_size = 1024**1024)
        print(bin_wave)
        with open('data.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(bin_wave)
        break
    counter.print()
    sleep(2)
    
scope.close()
rm.close()

