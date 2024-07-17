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
CH1_SCALE = 9 # mV
CH2_SCALE = 170 # mV
CH2_TRIGGER_LEVEL = -100 # mV

# 横軸の設定（トレードオフの関係があるので注意）
RECORD_LENGTH = 1.25e3 # 1shot分のpt数
TIME_GRID_LENGTH = 10 # ns
SAMPLERATE = 12.5e9 # Hz (6.25GHz)

# データ数
MAX_COUNT = 10 # 崩壊の測定回数
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
    "HORizontal:MODE MANual", # マニュアルモードに設定
    f"HORizontal:MODE:RECOrdlength {RECORD_LENGTH}" , # レコード長を設定
    f"HORizontal:SAMPLERate {SAMPLERATE}", # サンプリングレートを設定
    f"HORizontal:SCAle {TIME_GRID_LENGTH}e-9", # 横軸のスケールを設定
    "HORizontal:POSition 70", # センター

    # VERTICALの設定
    f"CH1:SCAle {CH1_SCALE}e-3", # 縦軸のスケールを設定
    f"CH2:SCAle {CH2_SCALE}e-3",
    "CH1:POSition 4.0", # 4 grid分ずらす
    "CH2:POSition 4.0",

    # TRIGGERの設定
    "TRIGger:A:EDGE:SLOpe FALL", # トリガーの経ち下がりでトリガー
    "TRIGger:A:EDGE:SOUrce CH2", # 2つ目のトリガーのソースをCH2に設定
    f"TRIGger:A:LEVel:CH2 {CH2_TRIGGER_LEVEL}e-3",
]

config_command = [
    "DATa:ENCdg ASCIi", # データのエンコードをASCIIに設定
    "DATa:SOUrce CH1", # データのソースをCH1に設定
    # "DATa:STARt?", # データの開始位置 デフォルトで1
    # 'DATa:STOP?',  # データの終了位置 1shot分のpt数
]


run_command(scope, init_command)
sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)
run_command(scope, config_command)
sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)    
filename = get_filename()
create_csv(filename, ['TIME', 'CH1'])
sleep(1) # 同期するまで待つ(TODO: *OPC?でダメだった)
create_metadata(scope, filename)

for i in range(MAX_COUNT):
    try:
        print(f"------------------------\n{i+1}回目の計測\n------------------------")
        get_waveform_1Ch(scope, filename)
    
    except KeyboardInterrupt:
        print("コマンドを停止しました。")
        break
print("計測を終了します。")

scope.close()
rm.close()