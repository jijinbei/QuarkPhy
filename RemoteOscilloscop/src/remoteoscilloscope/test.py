import pyvisa
import os
from dotenv import load_dotenv

# PCのWifi環境はオシロと同じネットワークに接続しているか？
load_dotenv()

IP_ADDRESS = os.getenv('IP_ADDRESS')
ipaddr = f'TCPIP::{IP_ADDRESS}::INSTR'

rm = pyvisa.ResourceManager('@py')
scope = rm.open_resource(ipaddr)

a = scope.query("TRIGger:A:UPPerthreshold:CH1?")
print(a)

scope.close()
rm.close()