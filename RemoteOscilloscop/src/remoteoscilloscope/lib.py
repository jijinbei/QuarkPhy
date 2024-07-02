import pyvisa

class Converter:
    def __init__(self, scope: pyvisa.Resource):
        # 1;8;BINARY;RI;INTEGER;LSB;1000000;Y;LINEAR;"s";4.0E-9;0.0E+0;0;"V";4.0000E-3;0.0E+0;0.0E+0;TIME;ANALOG;0.0E+0;0.0E+0;0.0E+0;1\n
        # scope.query(":WFMOutpre?")
        # self.wfm_record = int(scope.query('WFMOutpre:NR_Pt?'))
        # self.pre_trig_record = int(scope.query('WFMOutpre:PT_Off?'))
        self.t_scale = float(scope.query('WFMOutpre:XINcr?'))
        # self.t_sub = float(scope.query('WFMOutpre:XZEro?')) # sub-sample trigger correction
        # self.v_scale = float(scope.query('WFMOutpre:YMUlt?')) # volts / level
        # self.v_off = float(scope.query('WFMOutpre:YZEro?')) # reference voltage
        # self.v_pos = float(scope.query('WFMOutpre:YOFf?')) # reference position (level)
    
    def total_time(self):
        return self.t_scale * self.wfm_record

class Counter:
    def __init__(self):
        self.count = 0
    def print(self):
        print(f"Waiting{"."*(self.count%10+1)}")
        self.count += 1
        
def run_command(scope, command):
    for c in command:
        if '?' in c: # クエリの場合
            print(scope.query(c))
        else: # コマンドの場合
            scope.write(c)
