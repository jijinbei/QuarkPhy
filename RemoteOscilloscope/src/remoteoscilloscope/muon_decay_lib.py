import pyvisa
import numpy as np
import datetime
import os
import csv

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
    bin_wave = scope.query_ascii_values("CURVe?")
    scaled_wave = converter.get_scaled_wave(bin_wave) # 縦軸のスケールを取得
    return scaled_time, scaled_wave

def get_filename():
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    filename = f"{now.strftime('%Y%m%d')}.csv"
    return filename

def make_csv(filename: str):
    if not os.path.exists(filename):
        with open(filename, mode="w") as f:
            header = ['TIME', 'CH1', 'CH2']
            writer = csv.writer(f)
            writer.writerow(header)
    else:
        print(f"{filename}が存在します。")
        print("ファイル名を書き換えてください。")
        print("プログラムを終了します。")
        exit()
        
def write_csv(data: tuple, filename: str):
    t, v1, v2 = data
    with open(filename, mode="+a") as f:
        writer = csv.writer(f)
        for i in range(len(t)):
            writer.writerow([t[i], v1[i], v2[i]])

def make_metadata(scope: pyvisa.resources.MessageBasedResource, filename: str):
    metafile = "meta_" + filename
    make_csv(metafile)
    with open(metafile) as f:
        writer = csv.writer(f)
        writer.writerow(["WFMOutpre:NR_Pt?", scope.query('WFMOutpre:NR_Pt?')])
        writer.writerow(["WFMOutpre:PT_Off?", scope.query('WFMOutpre:PT_Off?')])
        writer.writerow(["WFMOutpre:XINcr?", scope.query('WFMOutpre:XINcr?')])
        writer.writerow(["WFMOutpre:XZEro?", scope.query('WFMOutpre:XZEro?')])
        writer.writerow(["WFMOutpre:YMUlt?", scope.query('WFMOutpre:YMUlt?')])
        writer.writerow(["WFMOutpre:YZEro?", scope.query('WFMOutpre:YZEro?')])
        writer.writerow(["WFMOutpre:YOFf?", scope.query('WFMOutpre:YOFf?')])
    