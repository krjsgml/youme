from bluetooth import *
soc= BluetoothSocket( RFCOMM )
try:
    soc.connect(("98:DA:60:0A:F8:2B", 1))
    print("connect success")
except Exception as e:
    print(e)
while True:
    msg = input()
    soc.send(msg+'\n')
    if msg=='z':
        break
soc.close()