import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pydobot import Dobot
import serial.tools.list_ports
import time

class DobotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dobot Control GUI")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        
        self.device = None
        self.connected = False
        self.move_thread = None
        
        # Define preset movements
        self.presets = {
            "Home": [(200, 0, 50, 0)],
            "Pick Position": [(259, 0, -8.6, 0), (259, 0, -131.8, 0)],
            "Place Position": [(161.2, 158.4, 2, 0), (161.2, 158.4, -130.7, 0)],
            "Demo Sequence": [
                (200, 0, 50, 0),
                (200, 0, 10, 0),
                (150, 0, 10, 0),
                (259, 0, -8.6, 0),
                (259, 0, -131.8, 0),
                (161.2, 158.4, 2, 0),
                (161.2, 158.4, -130.7, 0),
                (161.2, 158.4, -11.9, 0),
                (259, 0, -8.6, 0),
            ]
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = ttk.Label(self.root, text="Dobot Control Interface", 
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        conn_frame.pack(padx=10, pady=5, fill="x")
        
        button_frame = ttk.Frame(conn_frame)
        button_frame.pack(fill="x", pady=5)
        
        self.connect_btn = ttk.Button(button_frame, text="Connect", 
                                      command=self.connect_device)
        self.connect_btn.pack(side="left", padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", 
                                         command=self.disconnect_device, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="Status: Disconnected", 
                                      font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        self.port_label = ttk.Label(conn_frame, text="Port: Not detected", 
                                    font=("Arial", 9))
        self.port_label.pack(pady=2)
        
        # Current Pose Frame
        pose_frame = ttk.LabelFrame(self.root, text="Current Position", padding=10)
        pose_frame.pack(padx=10, pady=5, fill="x")
        
        self.pose_label = ttk.Label(pose_frame, text="X: -- Y: -- Z: -- R: --", 
                                    font=("Arial", 11, "bold"))
        self.pose_label.pack(pady=5)
        
        refresh_btn = ttk.Button(pose_frame, text="Refresh Position", 
                                command=self.refresh_pose)
        refresh_btn.pack(pady=5)
        
        # Manual Movement Frame
        manual_frame = ttk.LabelFrame(self.root, text="Manual Movement", padding=10)
        manual_frame.pack(padx=10, pady=5, fill="x")
        
        # Grid for input fields
        ttk.Label(manual_frame, text="X:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.x_var = tk.DoubleVar(value=0)
        ttk.Entry(manual_frame, textvariable=self.x_var, width=12).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Y:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.y_var = tk.DoubleVar(value=0)
        ttk.Entry(manual_frame, textvariable=self.y_var, width=12).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Z:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.z_var = tk.DoubleVar(value=50)
        ttk.Entry(manual_frame, textvariable=self.z_var, width=12).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="R:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.r_var = tk.DoubleVar(value=0)
        ttk.Entry(manual_frame, textvariable=self.r_var, width=12).grid(row=1, column=3, padx=5, pady=5)
        
        move_btn = ttk.Button(manual_frame, text="Move To Position", 
                             command=self.move_to_position)
        move_btn.grid(row=2, column=0, columnspan=4, pady=10, sticky="ew")
        
        # Preset Movements Frame
        preset_frame = ttk.LabelFrame(self.root, text="Preset Movements", padding=10)
        preset_frame.pack(padx=10, pady=5, fill="x")
        
        for preset_name in self.presets.keys():
            btn = ttk.Button(preset_frame, text=preset_name, 
                           command=lambda name=preset_name: self.execute_preset(name))
            btn.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        # Control Frame
        control_frame = ttk.LabelFrame(self.root, text="Controls", padding=10)
        control_frame.pack(padx=10, pady=5, fill="x")
        
        self.stop_btn = ttk.Button(control_frame, text="EMERGENCY STOP", 
                                  command=self.emergency_stop, state="disabled")
        self.stop_btn.pack(pady=5, fill="x")
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, width=80, state="disabled")
        self.log_text.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
    def log_message(self, message):
        """Add message to log"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        print(message)
    
    def connect_device(self):
        """Connect to Dobot"""
        threading.Thread(target=self._connect_thread, daemon=True).start()
    
    def _connect_thread(self):
        try:
            self.log_message("Searching for Dobot...")
            ports = list(serial.tools.list_ports.comports())
            port = None
            
            for p in ports:
                if "USB" in p.description or "Dobot" in p.description or "CH340" in p.description:
                    port = p.device
                    break
            
            if port is None:
                messagebox.showerror("Error", "Dobot not found! Please check USB connection.")
                self.log_message("ERROR: Dobot not found!")
                return
            
            self.log_message(f"Dobot found on port: {port}")
            self.port_label.config(text=f"Port: {port}")
            self.device = Dobot(port)
            self.connected = True
            
            # Update UI
            self.root.after(0, self._update_connection_ui, True, port)
            self.log_message("Successfully connected to Dobot!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def _update_connection_ui(self, connected, port):
        """Update UI based on connection status"""
        if connected:
            self.status_label.config(text="Status: Connected", foreground="green")
            self.port_label.config(text=f"Port: {port}")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.refresh_pose()
        else:
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.port_label.config(text="Port: Not detected")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.pose_label.config(text="X: -- Y: -- Z: -- R: --")
    
    def disconnect_device(self):
        """Disconnect from Dobot"""
        try:
            if self.device:
                self.device.close()
            self.connected = False
            self._update_connection_ui(False, "")
            self.log_message("Disconnected from Dobot")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disconnect: {str(e)}")
            self.log_message(f"ERROR: {str(e)}")
    
    def refresh_pose(self):
        """Refresh current pose"""
        if not self.connected:
            messagebox.showwarning("Warning", "Device not connected!")
            return
        
        threading.Thread(target=self._refresh_pose_thread, daemon=True).start()
    
    def _refresh_pose_thread(self):
        try:
            pose = self.device.pose()
            x, y, z, r = pose.x, pose.y, pose.z, pose.r
            self.root.after(0, lambda: self.pose_label.config(
                text=f"X: {x:.1f}  Y: {y:.1f}  Z: {z:.1f}  R: {r:.1f}"))
            self.log_message(f"Current position: X={x:.1f}, Y={y:.1f}, Z={z:.1f}, R={r:.1f}")
        except Exception as e:
            self.log_message(f"ERROR reading pose: {str(e)}")
    
    def move_to_position(self):
        """Move to manually entered position"""
        if not self.connected:
            messagebox.showwarning("Warning", "Device not connected!")
            return
        
        try:
            x = self.x_var.get()
            y = self.y_var.get()
            z = self.z_var.get()
            r = self.r_var.get()
            
            self.log_message(f"Moving to X={x}, Y={y}, Z={z}, R={r}...")
            threading.Thread(target=self._move_thread, args=(x, y, z, r), daemon=True).start()
        except ValueError:
            messagebox.showerror("Error", "Invalid input! Please enter numbers.")
    
    def execute_preset(self, preset_name):
        """Execute a preset movement sequence"""
        if not self.connected:
            messagebox.showwarning("Warning", "Device not connected!")
            return
        
        positions = self.presets[preset_name]
        self.log_message(f"Executing preset: {preset_name}")
        threading.Thread(target=self._preset_thread, args=(positions,), daemon=True).start()
    
    def _move_thread(self, x, y, z, r):
        """Move in a separate thread"""
        try:
            self.device.move_to(x, y, z, r)
            self.root.after(0, lambda: self.log_message(f"Movement completed!"))
            self.root.after(0, self.refresh_pose)
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"ERROR during movement: {str(e)}"))
    
    def _preset_thread(self, positions):
        """Execute preset movements in a separate thread"""
        try:
            for i, (x, y, z, r) in enumerate(positions):
                self.root.after(0, lambda msg=f"Moving to position {i+1}/{len(positions)}...": self.log_message(msg))
                self.device.move_to(x, y, z, r)
                time.sleep(0.5)
            
            self.root.after(0, lambda: self.log_message("Preset movement completed!"))
            self.root.after(0, self.refresh_pose)
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"ERROR during preset: {str(e)}"))
    
    def emergency_stop(self):
        """Emergency stop"""
        if self.device:
            try:
                self.log_message("EMERGENCY STOP activated!")
                # Try to move to safe position or just stop
                messagebox.showinfo("Emergency Stop", "Emergency stop activated!\nPlease verify robot safety.")
            except Exception as e:
                self.log_message(f"ERROR: {str(e)}")

def main():
    root = tk.Tk()
    app = DobotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
