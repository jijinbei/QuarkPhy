import pyvisa
from dotenv import load_dotenv
import os
import time
import datetime

load_dotenv()

IP_ADDRESS = os.getenv('IP_ADDRESS')
ipaddr = f'TCPIP0::{IP_ADDRESS}::INSTR'

rm = pyvisa.ResourceManager('@py')
inst = rm.open_resource(ipaddr)

del inst.timeout #オシロスコープのタイムアウトを無効にする

#オシロスコープの内蔵HDにテンポラリのキャプチャ画像を保存
inst.write('SAVE:IMAGe \"C:/Temp.png\"')

#画像のキャプチャ処理が終了するまで待つ
while inst.query('*OPC?')[0]!="1":
    print("Waiting")
    time.sleep(10)

#保存された画像ファイルをPC側へ読み出す
inst.write('FILESystem:READFile \"C:/Temp.png\"')
img_data = inst.read_raw()

#PC側に保存する際にdatetimeモジュールを使い、日付＋時間のファイル名で保存する
dt = datetime.datetime.now()
filename = dt.strftime("IMG_%Y%m%d_%H%M%S.png")
file = open(filename,"wb")
file.write(img_data)
file.close()


#測定終了後にオシロスコープとの通信を切断する
inst.close()
rm.close()