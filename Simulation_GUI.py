import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import can
import cantools
from cantools.database import Database
from cantools.database.can import Message, Signal
from cantools.database.conversion import BaseConversion
import threading
import time

# ==============================================================================
# 0. DATABASE DEFINITION
# ==============================================================================
def load_database():
    dbc_path = r"D:/Workspace/Embedded/CanSimulate/Sample_DBC_Kvaser.dbc"
    try:
        db = cantools.database.load_file(dbc_path)
        print(f"Loaded DBC: {dbc_path}")
        return db
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load DBC: {e}")
        return None

# ==============================================================================
# 1. NODE CLASSES (LOGIC)
# ==============================================================================

class BaseNode(ttk.LabelFrame):
    def __init__(self, parent, name, bus, db):
        super().__init__(parent, text=name, padding=10)
        self.name = name
        self.bus = bus
        self.db = db
        # Cache IDs for easier lookup in receive loop
        self.ids = {}
        if self.db:
            try:
                self.ids['Engine_Control'] = self.db.get_message_by_name('Engine_Control').frame_id
                self.ids['ABS_WheelSpeed'] = self.db.get_message_by_name('ABS_WheelSpeed').frame_id
                self.ids['Ignition_State'] = self.db.get_message_by_name('Ignition_State').frame_id
            except KeyError as e:
                print(f"Warning: Message {e} not found in DBC")
        
        self.create_ui()

    def create_ui(self):
        pass

    def send(self, msg_name, data_dict):
        if not self.bus:
            print(f"[{self.name}] Error: Bus not connected")
            return
        
        try:
            msg_def = self.db.get_message_by_name(msg_name)
            data = msg_def.encode(data_dict)
            msg = can.Message(arbitration_id=msg_def.frame_id, data=data, is_extended_id=False)
            self.bus.send(msg)
            print(f"[{self.name}] Sent {msg_name}: {data_dict}")
        except Exception as e:
            print(f"[{self.name}] Send Error: {e}")

    def on_receive(self, msg_id, data_dict):
        pass

class ECM_Node(BaseNode):
    def create_ui(self):
        # Sends RPM
        ttk.Label(self, text="RPM:").grid(row=0, column=0)
        self.rpm_var = tk.IntVar(value=1000)
        self.rpm_scale = tk.Scale(self, from_=0, to=8000, orient="horizontal", variable=self.rpm_var, command=self.update_rpm_label)
        self.rpm_scale.grid(row=0, column=1)
        self.rpm_label_val = ttk.Label(self, text="1000")
        self.rpm_label_val.grid(row=0, column=2)

        ttk.Button(self, text="Send Engine Control", command=self.send_rpm).grid(row=1, column=0, columnspan=3, pady=5)

        # Auto Control
        self.auto_var = tk.BooleanVar(value=False)
        self.auto_chk = ttk.Checkbutton(self, text="Auto Engine Control", variable=self.auto_var, command=self.toggle_auto)
        self.auto_chk.grid(row=2, column=0, columnspan=2, sticky='w')
        
        self.auto_interval = tk.IntVar(value=100)
        tk.Spinbox(self, from_=10, to=5000, increment=10, textvariable=self.auto_interval, width=5).grid(row=2, column=2)

        # Receives Ignition
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew', pady=5)
        ttk.Label(self, text="Received Status:").grid(row=4, column=0, sticky='w')
        self.status_lbl = ttk.Label(self, text="Ignition: -- | Speed: --")
        self.status_lbl.grid(row=4, column=1, columnspan=2, sticky='w')

        self.sweeping_up = True
        self.sweep_step = 100

    def update_rpm_label(self, val):
        self.rpm_label_val.config(text=str(int(float(val))))

    def send_rpm(self):
        self.send('Engine_Control', {'RPM': self.rpm_var.get()})

    def toggle_auto(self):
        if self.auto_var.get():
            self.auto_sweep()

    def auto_sweep(self):
        if not self.auto_var.get():
            return

        current = self.rpm_var.get()
        max_rpm = 65535
        min_rpm = 0
        
        if self.sweeping_up:
            current += self.sweep_step
            if current >= max_rpm:
                current = max_rpm
                self.sweeping_up = False
        else:
            current -= self.sweep_step
            if current <= min_rpm:
                current = min_rpm
                self.sweeping_up = True
        
        self.rpm_var.set(current)
        self.update_rpm_label(current)
        self.send_rpm()

        try:
            delay = int(self.auto_interval.get())
        except:
            delay = 100
        
        self.after(delay, self.auto_sweep)

    def on_receive(self, msg_id, data):
        if msg_id == self.ids.get('Ignition_State'): 
            ign = data.get('Ignition_Status')
            current = self.status_lbl.cget("text").split("|")[1] 
            self.status_lbl.config(text=f"Ignition: {ign} |{current}")
        elif msg_id == self.ids.get('ABS_WheelSpeed'):
            spd = data.get('FrontWheelSpeed')
            current = self.status_lbl.cget("text").split("|")[0]
            self.status_lbl.config(text=f"{current}| Speed: {spd:.1f}")

class ABS_Node(BaseNode):
    def create_ui(self):
        # Sends Wheel Speed
        ttk.Label(self, text="Front Spd:").grid(row=0, column=0)
        self.f_spd = tk.DoubleVar(value=60.0)
        tk.Spinbox(self, from_=0, to=255, increment=1, textvariable=self.f_spd, width=5).grid(row=0, column=1)

        ttk.Label(self, text="Rear Spd:").grid(row=1, column=0)
        self.r_spd = tk.DoubleVar(value=60.0)
        tk.Spinbox(self, from_=0, to=255, increment=1, textvariable=self.r_spd, width=5).grid(row=1, column=1)

        ttk.Button(self, text="Send Wheel Speed", command=self.send_speed).grid(row=2, column=0, columnspan=2, pady=5)

        # Auto Control
        f_auto = ttk.Frame(self)
        f_auto.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        self.auto_var = tk.BooleanVar(value=False)
        self.auto_chk = ttk.Checkbutton(f_auto, text="Auto Wheel Speed", variable=self.auto_var, command=self.toggle_auto)
        self.auto_chk.pack(side='left')
        
        self.auto_interval = tk.IntVar(value=100)
        tk.Spinbox(f_auto, from_=10, to=5000, increment=10, textvariable=self.auto_interval, width=5).pack(side='right')

        # Receives RPM
        ttk.Separator(self, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)
        self.rpm_display = ttk.Label(self, text="RPM: --", foreground="black")
        self.rpm_display.grid(row=5, column=0, columnspan=2)
        
        self.sweeping_up = True
        self.sweep_step = 2.0

    def toggle_auto(self):
        if self.auto_var.get():
            self.auto_sweep()

    def auto_sweep(self):
        if not self.auto_var.get():
            return

        current = self.f_spd.get()
        max_spd = 255.0
        min_spd = 0.0
        
        if self.sweeping_up:
            current += self.sweep_step
            if current >= max_spd:
                current = max_spd
                self.sweeping_up = False
        else:
            current -= self.sweep_step
            if current <= min_spd:
                current = min_spd
                self.sweeping_up = True
        
        self.f_spd.set(current)
        self.r_spd.set(current) # Sync both
        self.send_speed()

        try:
            delay = int(self.auto_interval.get())
        except:
            delay = 100
        
        self.after(delay, self.auto_sweep)

    def send_speed(self):
        self.send('ABS_WheelSpeed', {
            'FrontWheelSpeed': self.f_spd.get(),
            'RearLeftWheelSpeed': self.r_spd.get()
        })

    def on_receive(self, msg_id, data):
        if msg_id == self.ids.get('Engine_Control'):
            rpm = data.get('RPM')
            color = "red" if rpm > 5000 else "black"
            text = f"RPM: {rpm} (High!)" if rpm > 5000 else f"RPM: {rpm}"
            self.rpm_display.config(text=text, foreground=color)

class Cluster_Node(BaseNode):
    def create_ui(self):
        # Sends Ignition
        self.ign_var = tk.IntVar(value=0)
        ttk.Checkbutton(self, text="Ignition ON", variable=self.ign_var, command=self.send_ign).grid(row=0, column=0, columnspan=2)

        # Auto Control
        self.auto_var = tk.BooleanVar(value=False)
        self.auto_chk = ttk.Checkbutton(self, text="Auto Ign", variable=self.auto_var, command=self.toggle_auto)
        self.auto_chk.grid(row=1, column=0, sticky='w')
        
        self.auto_interval = tk.IntVar(value=1000)
        tk.Spinbox(self, from_=100, to=5000, increment=100, textvariable=self.auto_interval, width=5).grid(row=1, column=1)

        # Display
        ttk.Separator(self, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        ttk.Label(self, text="DASHBOARD", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2)
        
        self.lbl_rpm = ttk.Label(self, text="RPM: 0", font=("Arial", 12))
        self.lbl_rpm.grid(row=4, column=0, pady=5)
        
        self.lbl_spd = ttk.Label(self, text="0 km/h", font=("Arial", 16, "bold"))
        self.lbl_spd.grid(row=4, column=1, pady=5)

    def toggle_auto(self):
        if self.auto_var.get():
            self.auto_sweep()

    def auto_sweep(self):
        if not self.auto_var.get():
            return

        # Toggle 0 -> 1 -> 0
        current = self.ign_var.get()
        new_val = 1 if current == 0 else 0
        self.ign_var.set(new_val)
        self.send_ign()

        try:
            delay = int(self.auto_interval.get())
        except:
            delay = 1000
        
        self.after(delay, self.auto_sweep)

    def send_ign(self):
        self.send('Ignition_State', {'Ignition_Status': self.ign_var.get()})

    def on_receive(self, msg_id, data):
        if msg_id == self.ids.get('Engine_Control'):
            self.lbl_rpm.config(text=f"RPM: {data.get('RPM')}")
        elif msg_id == self.ids.get('ABS_WheelSpeed'):
            self.lbl_spd.config(text=f"{(data.get('FrontWheelSpeed') + data.get('RearLeftWheelSpeed'))/2:.1f} km/h")

class Gateway_Node(BaseNode):
    def create_ui(self):
        self.log = scrolledtext.ScrolledText(self, width=30, height=10, state='disabled', font=("Consolas", 8))
        self.log.pack(fill='both', expand=True)

    def on_receive(self, msg_id, data):
        # Simply Log and "Forward"
        try:
            msg_name = self.db.get_message_by_frame_id(msg_id).name
        except:
            msg_name = "Unknown"
        self.log_msg(f"RELAY -> CAN2: {msg_name} ({hex(msg_id)})")

    def log_msg(self, txt):
        self.log.config(state='normal')
        self.log.insert(tk.END, txt + "\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')

# ==============================================================================
# 2. MAIN APP
# ==============================================================================

class CarSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automotive Multi-Node Simulator")
        self.geometry("900x600")

        self.db = load_database()
        self.bus = None
        self.running = True

        self.setup_header()
        self.setup_nodes()
        
        # Start Thread
        self.rx_thread = threading.Thread(target=self.rx_loop, daemon=True)
        self.rx_thread.start()

    def setup_header(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill='x')
        ttk.Label(frame, text="Interface: kvaser, Channel: 0").pack(side='left')
        ttk.Button(frame, text="Connect", command=self.connect).pack(side='left', padx=10)
        self.lbl_status = ttk.Label(frame, text="Disconnected", foreground="red")
        self.lbl_status.pack(side='left')

    def setup_nodes(self):
        main_grid = ttk.Frame(self)
        main_grid.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Grid Layout: 2x2
        self.ecm = ECM_Node(main_grid, "ECM (Engine)", self.bus, self.db)
        self.ecm.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.abs = ABS_Node(main_grid, "ABS (Brake)", self.bus, self.db)
        self.abs.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.cluster = Cluster_Node(main_grid, "Instrument Cluster", self.bus, self.db)
        self.cluster.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.gateway = Gateway_Node(main_grid, "Gateway (Router)", self.bus, self.db)
        self.gateway.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        main_grid.columnconfigure(0, weight=1)
        main_grid.columnconfigure(1, weight=1)
        main_grid.rowconfigure(0, weight=1)
        main_grid.rowconfigure(1, weight=1)

    def connect(self):
        try:
            # Using Kvaser channel 0 by default as per context
            # receive_own_messages=True is CRITICAL for a single-app simulator to see what it sent
            self.bus = can.Bus(interface='kvaser', channel=0, bitrate=500000, receive_own_messages=True)
            self.lbl_status.config(text="Connected", foreground="green")
            
            # Update bus ref for all nodes
            self.ecm.bus = self.bus
            self.abs.bus = self.bus
            self.cluster.bus = self.bus
            self.gateway.bus = self.bus
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def rx_loop(self):
        while self.running:
            if self.bus:
                try:
                    msg = self.bus.recv(timeout=0.1)
                    if msg:
                        try:
                            decoded = self.db.decode_message(msg.arbitration_id, msg.data)
                            # Dispatch to ALL nodes
                            self.root_after(0, self.ecm.on_receive, msg.arbitration_id, decoded)
                            self.root_after(0, self.abs.on_receive, msg.arbitration_id, decoded)
                            self.root_after(0, self.cluster.on_receive, msg.arbitration_id, decoded)
                            self.root_after(0, self.gateway.on_receive, msg.arbitration_id, decoded)
                        except Exception as decode_err:
                            pass # Unknown message or decode error
                except Exception as e:
                    print(f"Rx Loop Error: {e}")
    
    def root_after(self, delay, func, *args):
        self.after(delay, func, *args)

if __name__ == "__main__":
    app = CarSimulationApp()
    app.mainloop()
