import pyvisa
import os
from dotenv import load_dotenv

# PCのWifi環境はオシロと同じネットワークに接続しているか？
load_dotenv()

IP_ADDRESS = os.getenv('IP_ADDRESS')
ipaddr = f'TCPIP::{IP_ADDRESS}::INSTR'

rm = pyvisa.ResourceManager('@py')
inst = rm.open_resource(ipaddr)


# オシロスコープの機種
print(inst.query('*IDN?'))

inst.close()
rm.close()