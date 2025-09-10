# Humanizer - Desktop Text to Speech (TTS)

Humanizer is a simple, responsive, and unlimited desktop TTS application.  
It lets you preview spoken text in real time, adjust voice settings, and export audio to files.

The app is lightweight, cross-platform, and works on Linux and Windows.

---

## Features
- Clean and minimal UI, responsive to all screen sizes  
- Live preview of text before exporting  
- Save or export audio in multiple formats  
- Adjustable voice settings (pitch, rate, volume)  
- Works offline once installed  
- Cross-platform support (Windows & Linux/WSL)  

---

## Installation

Follow these steps carefully. No prior experience needed.

### Linux / WSL
```bash
# Clone the repository
git clone https://github.com/nasratulnayem/Humanizer-tts-unlimited-free.git
cd Humanizer-tts-unlimited-free

# Run the installer (sets up Python, pip, venv, and dependencies)
sudo chmod +x install.sh run.sh
./install.sh

# Start the app
./run.sh
````

### Windows

```bat
:: Clone the repository
git clone https://github.com/nasratulnayem/Humanizer-tts-unlimited-free.git
cd Humanizer-tts-unlimited-free

:: Run the installer (sets up Python, pip, venv, and dependencies)
install.bat

:: Start the app
run.bat
```

---

## Uninstallation

### Linux / WSL

```bash
./uninstall.sh
```

### Windows

Delete the following manually:

* `.venv` folder
* `build/` and `dist/` folders
* `Humanizer.spec` (if created)

---

## Build Executable (Windows only)

```bat
build_exe.bat
```

The output will be created in:

```
dist/Humanizer.exe
```

---

## Project Structure

* `main.py` - Main application with UI and logic
* `install.sh` - One-click setup script for Linux/WSL
* `install.bat` - One-click setup script for Windows
* `run.sh` - Start the app on Linux/WSL
* `run.bat` - Start the app on Windows
* `uninstall.sh` - Uninstall script for Linux/WSL
* `build_exe.bat` - Build a standalone Windows executable
* `requirements.txt` - Python dependencies list

---

## Contributing

Pull requests and suggestions are welcome.
If you’d like to add new features (like more voice options or UI improvements), feel free to fork and submit.

---

## License

This project is licensed under the MIT License.
You are free to use, modify, and distribute with attribution.
