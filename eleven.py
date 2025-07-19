import os
import struct
import subprocess
import customtkinter as ctk
from tkinter import messagebox

# === Filesystem Constants ===
BLOCK_SIZE = 233
HEADER_MAGIC = b'\x9A\xC3\xF1\x11\x72\xD9'
VERSION = 1
HEADER_RESERVED = 4
CLEAR_SIZE = 10 * 1024 * 1024
BASE_OFFSET_MB = 100
SLOT_SPACING_MB = 5
NUM_SLOTS = 5

PIN_CODES = {
    0: "123456",
    1: "234567",
    2: "345678",
    3: "456789",
    4: "567890",
}


def pad_block(data: bytes) -> bytes:
    return data.ljust(BLOCK_SIZE, b'\x00')


def create_header(message_bytes: bytes) -> bytes:
    msg_len = len(message_bytes)
    if msg_len > (224 + BLOCK_SIZE * 45006):
        raise ValueError("Message too long.")
    header = HEADER_MAGIC
    header += struct.pack('>B', VERSION)
    header += struct.pack('>H', msg_len)
    header += b'\x00' * HEADER_RESERVED
    header += message_bytes[:224]
    return header.ljust(BLOCK_SIZE, b'\x00')


def get_slot_offset(slot_id: int) -> int:
    return (BASE_OFFSET_MB + slot_id * SLOT_SPACING_MB) * 1024 * 1024


def write_to_usb(device_path: str, message: str, slot_id: int):
    message_bytes = message.encode('utf-8')
    header_block = create_header(message_bytes)
    remaining = message_bytes[224:]
    offset = get_slot_offset(slot_id)

    with open(device_path, 'rb+') as usb:
        usb.seek(offset)
        usb.write(b'\x00' * CLEAR_SIZE)
        usb.seek(offset)
        usb.write(header_block)
        for i in range(0, len(remaining), BLOCK_SIZE):
            block = remaining[i:i + BLOCK_SIZE]
            usb.write(pad_block(block))


def wipe_slot(device_path: str, slot_id: int):
    offset = get_slot_offset(slot_id)
    with open(device_path, 'rb+') as usb:
        usb.seek(offset)
        usb.write(b'\x00' * CLEAR_SIZE)


def read_from_usb(device_path: str, slot_id: int) -> str:
    offset = get_slot_offset(slot_id)
    attempts = 0
    while attempts < 2:
        pin_input = ctk.CTkInputDialog(title="PIN Required", text=f"Enter PIN for slot {slot_id}:").get_input()
        if pin_input == PIN_CODES.get(slot_id):
            break
        attempts += 1

    if attempts == 2:
        wipe_slot(device_path, slot_id)
        raise ValueError("Access denied. Message deleted.")

    with open(device_path, 'rb') as usb:
        usb.seek(offset)
        block0 = usb.read(BLOCK_SIZE)
        if block0[:6] != HEADER_MAGIC:
            raise ValueError("Invalid or missing custom filesystem.")

        msg_len = struct.unpack('>H', block0[7:9])[0]
        message_bytes = bytearray()
        bytes_from_block0 = min(224, msg_len)
        message_bytes += block0[13:13 + bytes_from_block0]

        remaining_len = msg_len - bytes_from_block0
        while remaining_len > 0:
            next_block = usb.read(BLOCK_SIZE)
            take = min(BLOCK_SIZE, remaining_len)
            message_bytes += next_block[:take]
            remaining_len -= take

        return message_bytes[:msg_len].decode('utf-8')


def list_usb_devices() -> list:
    try:
        result = subprocess.run(['lsblk', '-b', '-o', 'NAME,TYPE,RM'], stdout=subprocess.PIPE, text=True)
        devices = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                name, dtype, rm = parts
                if dtype == 'disk' and rm == '1':
                    devices.append(f"/dev/{name}")
        return devices
    except:
        return []


def launch_gui():
    ctk.set_appearance_mode("dark")
    ctk.ThemeManager.appearance_mode = "dark"

    root = ctk.CTk()
    root.title("USB Message Tool")
    root.geometry("500x500")
    root.resizable(False, False)

    def update_status(text, color="gray"):
        status_label.configure(text=text, text_color=color)

    def handle_write():
        device = device_var.get()
        slot = int(slot_var.get())
        message = message_entry.get("1.0", "end").strip()
        if not device:
            messagebox.showerror("Error", "Select a USB device.")
            return
        if not message:
            messagebox.showerror("Error", "Message is empty.")
            return
        try:
            write_to_usb(device, message, slot)
            update_status("Message written.", "green")
        except Exception as e:
            update_status("Write error.", "red")
            messagebox.showerror("Write Error", str(e))

    def handle_read():
        device = device_var.get()
        slot = int(slot_var.get())
        if not device:
            messagebox.showerror("Error", "Select a USB device.")
            return
        try:
            msg = read_from_usb(device, slot)
            message_entry.delete("1.0", "end")
            message_entry.insert("1.0", msg)
            update_status("Message read.", "green")
        except Exception as e:
            update_status("Read error.", "red")
            messagebox.showerror("Read Error", str(e))

    def refresh_devices():
        device_menu.configure(values=list_usb_devices())
        update_status("🔄 Refreshed.")

    ctk.CTkLabel(root, text="USB Device:").pack(pady=(15, 2))
    device_var = ctk.StringVar()
    device_menu = ctk.CTkComboBox(root, variable=device_var, width=280, values=list_usb_devices())
    device_menu.pack()

    ctk.CTkButton(root, text="Refresh", command=refresh_devices).pack(pady=5)

    ctk.CTkLabel(root, text="Slot (0–4):").pack(pady=(15, 2))
    slot_var = ctk.StringVar(value="0")
    slot_menu = ctk.CTkComboBox(root, variable=slot_var, values=[str(i) for i in range(NUM_SLOTS)], width=80)
    slot_menu.pack()

    ctk.CTkLabel(root, text="Message:").pack(pady=(15, 2))
    message_entry = ctk.CTkTextbox(root, width=400, height=140)
    message_entry.pack(pady=5)

    btn_frame = ctk.CTkFrame(root)
    btn_frame.pack(pady=15)

    ctk.CTkButton(btn_frame, text="✍Write", command=handle_write, width=140).grid(row=0, column=0, padx=10)
    ctk.CTkButton(btn_frame, text="Read", command=handle_read, width=140).grid(row=0, column=1, padx=10)

    status_label = ctk.CTkLabel(root, text="", text_color="gray")
    status_label.pack()

    # Add Close Button
    ctk.CTkButton(root, text="Close App", command=root.destroy, fg_color="red", hover_color="darkred").pack(pady=(10, 20))

    root.mainloop()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw()

    class PinPrompt(ctk.CTkToplevel):
        def __init__(self, master):
            super().__init__(master)
            self.title("Enter PIN to Start")
            self.geometry("320x180")
            self.resizable(False, False)
            self.attempts = 0

            ctk.CTkLabel(self, text="Enter 6-digit PIN:").pack(pady=(20, 10))
            self.pin_entry = ctk.CTkEntry(self, show="*", width=180)
            self.pin_entry.pack()
            self.pin_entry.focus()

            self.status = ctk.CTkLabel(self, text="", text_color="red")
            self.status.pack(pady=(10, 5))

            ctk.CTkButton(self, text="Unlock", command=self.check_pin).pack(pady=10)

            self.protocol("WM_DELETE_WINDOW", self.quit_app)
            self.grab_set()
            self.master = master

        def check_pin(self):
            pin = self.pin_entry.get()
            if pin == "654321":
                self.destroy()
                self.master.destroy()
                launch_gui()
            else:
                self.attempts += 1
                self.status.configure(text="Incorrect PIN.")
                if self.attempts >= 2:
                    self.status.configure(text="Too many attempts. Self-damaging...")
                    self.after(1200, self.destroy_and_damage)

        def destroy_and_damage(self):
            try:
                script_path = os.path.abspath(__file__)
                with open(script_path, "wb") as f:
                    f.write(b"# Access denied\n" + os.urandom(512))
                os.remove(script_path)
            except:
                pass
            self.quit_app()

        def quit_app(self):
            self.master.destroy()
            self.destroy()
            exit()

    PinPrompt(root)
    root.mainloop()

here is the info and the error message
python3 ./eleven.py 
Traceback (most recent call last):
  File "/home/sunny/usb-project/new-filesystem/./eleven.py", line 4, in <module>
    import customtkinter as ctk
ModuleNotFoundError: No module named 'customtkinter'
