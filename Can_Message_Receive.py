import can
import cantools
import time

PortUSB = "kvaser"
CanChannel = 0
CAN_DBC_PATH = r"D:/Workspace/Embedded/CanSimulate/Sample_DBC_Kvaser.dbc"

def CAN_Configure():
    bus = can.Bus(channel=CanChannel, interface=PortUSB)
    db = cantools.database.load_file(CAN_DBC_PATH)
    return bus, db

def CAN_Receive(bus, db):
    cnt = 0
    while True:
        # Timeout suggests to python-can to return None if no message in x seconds,
        # allowing the loop to continue and check for other conditions (or signals to be caught)
        message = bus.recv(timeout=1.0)
        if message is not None:
            try:
                decoded = db.decode_message(message.arbitration_id, message.data)
                print("{} - {} - {} - {}".format(cnt, hex(message.arbitration_id), message.data.hex(), decoded))
                cnt += 1
            except Exception as e:
                # Fallback if decoding fails or message not in DB
                print("{} - {} - {} - (Decode error: {})".format(cnt, hex(message.arbitration_id), message.data.hex(), e))

def main():
    bus = None
    try:
        bus, db = CAN_Configure()
        print("Listening for CAN messages... Press Ctrl+C to stop.")
        CAN_Receive(bus, db)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if bus is not None:
            bus.shutdown()

if __name__ == "__main__":
    main()