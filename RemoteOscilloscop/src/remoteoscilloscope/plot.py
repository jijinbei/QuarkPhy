import numpy as np
import pyvisa
import csv
from dotenv import load_dotenv
import os
from time import sleep

load_dotenv()
IP_ADDRESS = os.getenv('IP_ADDRESS')
ipaddr = f'TCPIP::{IP_ADDRESS}::INSTR'
rm = pyvisa.ResourceManager('@py')
scope = rm.open_resource(ipaddr)

# scope.timeout = 10000 #オシロスコープのタイムアウトを無効にする

TIME_GRID_LENGTH = 4 # us
CH1_SCALE = 3 # mV
CH2_SCALE = 100 # mV
CH1_TRIGGER_LEVEL = -10 # mV
CH2_TRIGGER_LEVEL = -100 # mV
DELAY_TIME = 300 # ns
RESET_TIMEOUT = 30 # us

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
    "TRIGger:B:EDGE:SOUrce CH2", # 2つ目のトリガーのソースをCH2に設定
    f"TRIGger:A:LEVel:CH1 {CH1_TRIGGER_LEVEL}e-3", # トリガーレベルを設定
    f"TRIGger:B:LEVel:CH2 {CH2_TRIGGER_LEVEL}e-3",
    f"TRIGger:B:TIMe {DELAY_TIME}e-9", # トリガーの時間を設定
    "TRIGger:B:RESET:TYPe TIMEOut", # TIMEOUTの設定
    f"TRIGger:B:RESET:TIMEOut:TIMe {RESET_TIMEOUT}e-6", # TIMEOUTの時間を設定
]

def run_command(scope, command):
    for c in command:
        if '?' in c: # クエリの場合
            print(scope.query(c))
        else: # コマンドの場合
            scope.write(c)

run_command(scope, init_command)

scope.close()
rm.close()
