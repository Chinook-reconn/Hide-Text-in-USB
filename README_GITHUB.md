# 🔐 Eleven USB Message Tool

Eleven is a secure, slot-based USB message storage tool that writes messages **directly to raw USB block devices**. It includes a dark-mode GUI, PIN protection, and an optional self-destruct mechanism on failed access attempts.

---

## ✨ Features

- Write messages to USBs without using the filesystem
- PIN-protected slots (0–4), each with individual codes
- Messages hidden from file browsers (stored outside FS area)
- GUI interface built with `customtkinter`
- Auto self-destruct after failed PIN attempts
- Debian `.deb` installer with desktop icon support

---

## 📦 Installation

### 🔧 System Requirements

- Python 3.7+
- `python3-tk`
- `pip3`
- `lsblk` (usually included in `util-linux`)

Install system packages:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk util-linux
```

Install Python packages:

```bash
pip3 install -r requirements.txt
```

> Or use the `.deb` installer below for automated setup.

### 🧱 `.deb` Installer (Recommended)

Download and install the package:

```bash
sudo dpkg -i eleven_1.1.deb
```

This will:
- Install the app to `/usr/local/bin/eleven`
- Create a menu entry under "USB Message Tool"
- Install the required `customtkinter` package automatically

---

## 🚀 Usage

Run via terminal:

```bash
sudo eleven
```

Or launch **"USB Message Tool"** from your system menu.

---

## 🧰 How It Works

- Messages are stored at fixed byte offsets (`100MB + slot * 5MB`)
- Each message includes a magic header and is written block-by-block
- The app never touches the filesystem — ideal for hidden message storage

---

## 🔒 Security Notes

- Incorrect PIN attempts will wipe the message from its slot
- Self-destruct mechanism overwrites and deletes the script if bypass is attempted
- PINs are hardcoded per slot (can be customized)

---

## 📁 Project Structure

```
usbmsgtool/
├── usbmsgtool.py          # Main application script
├── requirements.txt       # Python requirements
├── eleven_1.1.deb         # Debian installer
├── usbmsgtool.desktop     # Launcher file (inside .deb)
└── eleven.png             # App icon
```

---

## 🧑‍💻 Author

Built by [Your Name] — feel free to contribute, fork, or adapt this project!

---

## 📜 License

MIT License (or choose your preferred open-source license)