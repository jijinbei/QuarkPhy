import pyvisa

# visa_address = 'USB0::1689::261::Q300209::0::INSTR'
rm = pyvisa.ResourceManager()
rm.list_resources()