[🇻🇳 Vietnamese Version](README_VI.md)

# CanSimulate - CAN Bus Simulation

This project provides tools for simulating and communicating on a CAN (Controller Area Network) bus using Python. It includes scripts for sending and receiving messages, as well as a comprehensive Graphical User Interface (GUI) that simulates various automotive ECUs.

## System Requirements

*   Python 3.x
*   Python Libraries:
    *   `python-can`
    *   `cantools`
    *   `tkinter` (usually included with Python on Windows)
*   CAN Hardware/Driver (defaults to `kvaser`, but configurable in the code).

Install necessary libraries:
```bash
pip install python-can cantools
```

## Project Structure

The project consists of 3 main source files located in `cantools/src/cantools`:

1.  **`Can_Message_Receive.py`**: A script to receive and decode CAN messages.
2.  **`Can_Message_Send.py`**: A script to simulate sending CAN messages.
3.  **`Simulation_GUI.py`**: A multi-node simulation GUI application (ECM, ABS, Cluster, Gateway).

---

## Module Details

### 1. Receive Messages (`Can_Message_Receive.py`)

This file establishes a connection to the CAN bus and listens for incoming messages in an infinite loop.

*   **Functionality**:
    *   Connects to interface `kvaser`, channel 0.
    *   Loads the DBC file (`Sample_DBC_Kvaser.dbc`) to decode signals.
    *   Prints the sequence number, ID, raw data (hex), and decoded data of received messages.
*   **Usage**: When you want to check if there is any traffic on the bus and see what the content is.

**How to run:**
```bash
python cantools/src/cantools/Can_Message_Receive.py
```

### 2. Send Messages (`Can_Message_Send.py`)

This file simulates broadcasting a specific sequence of messages onto the CAN network.

*   **Functionality**:
    *   Connects to interface `kvaser`, channel 1.
    *   Creates an `ABS_Wheel_Speed` message (ID 0x12C) with sample data.
    *   Sends 100 messages continuously with a 0.1s interval.
*   **Note**: This file is configured to use **Channel 1**. This is useful for testing communication between Channel 1 (Sender) and Channel 0 (Receiver/GUI) on the same device or PC.

**How to run:**
```bash
python cantools/src/cantools/Can_Message_Send.py
```

### 3. Simulation GUI (`Simulation_GUI.py`)

This is the main application, simulating a complete automotive CAN network system with virtual ECUs interacting with each other.

*   **Simulated Nodes**:
    *   **ECM (Engine Control Module)**: 
        *   Controls RPM via a slider.
        *   Receives Ignition status (from Cluster) and Speed (from ABS) for display.
    *   **ABS (Anti-lock Braking System)**: 
        *   Inputs and sends Front/Rear Wheel Speed.
        *   Receives RPM (from ECM) and displays a red warning if RPM is too high (>5000).
    *   **Cluster (Instrument Cluster)**: 
        *   Sends Ignition State (On/Off).
        *   Displays RPM and Vehicle Speed received from the CAN network, acting like a real dashboard.
    *   **Gateway**: 
        *   Acts as a monitor, logging all messages routed through the network.

*   **How it works**:
    *   The application connects to `kvaser` channel 0.
    *   Uses `receive_own_messages=True` mode so that virtual nodes within the same app can "hear" each other's messages.
    *   Uses a separate Thread to listen for incoming messages without freezing the GUI.

**How to run:**
```bash
python cantools/src/cantools/Simulation_GUI.py
```

## Configuration Notes

In the source code, the path to the DBC file is hardcoded:
`D:/Workspace/Embedded/CanSimulate/Sample_DBC_Kvaser.dbc`

If you move the project or run it on a different machine, please:
1.  Ensure the `.dbc` file exists.
2.  Update the `CAN_DBC_PATH` or `dbc_path` variable in the 3 Python files mentioned above to point to the correct location of your `.dbc` file.
