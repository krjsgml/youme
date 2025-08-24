import bluetooth

target_name = "HC-05"
target_address = "98:DA:60:0A:F8:2B"

nearby_devices = bluetooth.discover_devices()

for bdaddr in nearby_devices:
    if target_name == bluetooth.lookup_name(bdaddr):
        target_address = bdaddr
        break

if target_address is not None:
    print("Found target bluetooth device with address:", target_address)

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((target_address, 1))
    print("Connected.")

    try:
        while True:
            data = sock.recv(1024)
            if data:
                print("Received:", data.decode())
    except KeyboardInterrupt:
        print("\nDisconnected.")
    finally:
        sock.close()
else:
    print("Could not find target bluetooth device nearby")