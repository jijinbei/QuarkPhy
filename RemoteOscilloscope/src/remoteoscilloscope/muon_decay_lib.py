import pyvisa
import numpy as np
import datetime
import os
import csv
from time import sleep

class Converter:
    def __init__(self, scope: pyvisa.resources.MessageBasedResource):
        self.wfm_record = int(scope.query('WFMOutpre:NR_Pt?'))
        pre_trig_record = int(scope.query('WFMOutpre:PT_Off?'))
        t_scale = float(scope.query('WFMOutpre:XINcr?'))
        t_sub = float(scope.query('WFMOutpre:XZEro?')) # sub-sample trigger correction
        self.v_scale = float(scope.query('WFMOutpre:YMUlt?')) # volts / level
        self.v_off = float(scope.query('WFMOutpre:YZEro?')) # reference voltage
        self.v_pos = float(scope.query('WFMOutpre:YOFf?')) # reference position (level)
        
        self.total_time = t_scale * self.wfm_record
        self.t_start = (-pre_trig_record * t_scale) + t_sub
        self.t_stop = self.t_start + self.total_time

    def get_scaled_time(self):
        return np.linspace(self.t_start, self.t_stop, num=self.wfm_record, endpoint=False)
    
    def get_scaled_wave(self, bin_wave: np.array):
        unscaled_wave = np.array(bin_wave, dtype='double') # data type conversion
        return (unscaled_wave - self.v_pos) * self.v_scale + self.v_off

class Counter:
    def __init__(self):
        self.count = 0
    def print(self):
        print(f"Waiting{"."*(self.count%10+1)}")
        self.count += 1
        
def run_command(scope: pyvisa.resources.MessageBasedResource, command):
    for c in command:
        if '?' in c: # クエリの場合
            print(scope.query(c))
        else: # コマンドの場合
            scope.write(c)

def SAVe_DATa_SOUrce(ch: int, scope: pyvisa.resources.MessageBasedResource):
    scope.write(f"DATa:SOUrce CH{ch}")
    converter = Converter(scope)
    scaled_time = converter.get_scaled_time() # 横軸のスケールを取得  
    bin_wave = scope.query_ascii_values("CURVe?", container=np.array)
    scaled_wave = converter.get_scaled_wave(bin_wave) # 縦軸のスケールを取得
    return scaled_time, scaled_wave

def get_filename():
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    filename = f"{now.strftime('%Y%m%d')}.csv"
    return filename

def create_csv(filename: str, header: list):
    if not os.path.exists(filename):
        with open(filename, mode="w") as f:
            writer = csv.writer(f)
            if header == None:
                pass
            else:
                writer.writerow(header)
    else:
        print(f"{filename}が存在します。")
        print("ファイル名を書き換えてください。")
        print("プログラムを終了します。")
        exit()

def rm_new_line_code(string: str):
    return string.replace("\n", "")

# メタデータの例
# Model,MSO44
# Label,
# Waveform Type,ANALOG
# Horizontal Units,s
# Sample Interval,6.40000000e-10
# Record Length,156250
# Zero Index,149999.25000000
# Vertical Units,V
# FastFrame Count,50
# ANALOG_Thumbnail,
# yOffset,0.00000000e+00
# yPosition,4.24000000e+00
def create_metadata(scope: pyvisa.resources.MessageBasedResource, filename: str):
    metafile = "meta_" + filename
    if not os.path.exists(metafile):
        with open(metafile, mode="w") as f:
            writer = csv.writer(f)
            writer.writerow(["Sample Interval", rm_new_line_code(scope.query("WFMOutpre:XINcr?"))])
            writer.writerow(["Record Length", rm_new_line_code(scope.query("WFMOutpre:NR_Pt?"))])
            writer.writerow(["Zero Index", rm_new_line_code(scope.query("WFMOutpre:PT_Off?"))])
            writer.writerow(["yOffset", rm_new_line_code(scope.query("WFMOutpre:YZEro?"))])
            # writer.writerow(["yPosition", rm_new_line_code(scope.query("WFMOutpre:YOFf?"))])
    else:  
        print(f"{metafile}が存在します。")
        print("ファイル名を書き換えてください。")
        print("プログラムを終了します。")
        exit()

def add_csv_2Ch(data: tuple, filename: str):
    t, v1, v2 = data
    with open(filename, mode="+a") as f:
        writer = csv.writer(f)
        for i in range(len(t)):
            writer.writerow([t[i], v1[i], v2[i]])

def add_csv_1Ch(data: tuple, filename: str):
    t, v = data
    with open(filename, mode="+a") as f:
        writer = csv.writer(f)
        for i in range(len(t)):
            writer.writerow([t[i], v[i]])

# オシロスコープの状態
ACQuire_STATE = {
    "STOP": "0\n",
    "RUN": "1\n",
}

# データ取得(1Chと2Ch)
def get_waveform_2Ch(scope: pyvisa.resources.MessageBasedResource, filename: str):
    run_command(scope, ["ACQuire:STATE ON", "ACQuire:STOPAfter SEQuence"]) # single/seq mode"
    counter = Counter()
    while True:
        state = scope.query("ACQuire:STATE?")
        if state == ACQuire_STATE["STOP"]:
            print("Hit!!!!!")
            t, v_ch1 = SAVe_DATa_SOUrce(1, scope)
            _, v_ch2 = SAVe_DATa_SOUrce(2, scope)
            add_csv_2Ch((t, v_ch1, v_ch2), filename)
            break
        counter.print()
        sleep(2)

# データ取得(1Chのみ)
def get_waveform_1Ch(scope: pyvisa.resources.MessageBasedResource, filename: str):
    # 有効数字
    significant_digits = 6
    
    run_command(scope, ["ACQuire:STATE ON", "ACQuire:STOPAfter SEQuence"]) # single/seq mode"
    counter = Counter()
    while True:
        state = scope.query("ACQuire:STATE?")
        if state == ACQuire_STATE["STOP"]:
            print("Hit!!!!!")
            t, v_ch1 = SAVe_DATa_SOUrce(1, scope)
            t, v_ch1 = format_array_to_sci_notation(t, significant_digits), format_array_to_sci_notation(v_ch1, significant_digits)
            add_csv_1Ch((t, v_ch1), filename)
            break
        counter.print()
        sleep(2)

# 有効数字例
# -3.83988300e-05,5.92187500e-04
# -3.83980300e-05,4.70312500e-04
# -3.83972300e-05,8.75000000e-04
def format_array_to_sci_notation(arr, significant_digits):
    formatted_elements = [f"{x:.{significant_digits}e}" for x in arr]
    return formatted_elements
