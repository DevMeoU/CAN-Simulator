import can
import cantools
import time

PortUSB = "kvaser"
CanChannel = 1
AMOUNT_OF_MESSAGES = 100
CAN_DBC_PATH = r"D:/Workspace/Embedded/CanSimulate/Sample_DBC_Kvaser.dbc"

def CAN_Configure():
    bus = can.Bus(channel=CanChannel, interface=PortUSB)
    db = cantools.database.load_file(CAN_DBC_PATH)
    return bus, db

def main():
    bus, db = CAN_Configure()

    ABS_Wheel_Speed = can.Message(arbitration_id=0x12C, data=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08], is_extended_id=False)

    for i in range(AMOUNT_OF_MESSAGES):
        bus.send(ABS_Wheel_Speed)
        print(f"Sent message {i} - {ABS_Wheel_Speed}")
        time.sleep(0.1)
    bus.shutdown()

if __name__ == "__main__":
    main()