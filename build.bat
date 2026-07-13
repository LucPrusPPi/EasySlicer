@echo off
setlocal
cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
  python -m venv venv
  call venv\Scripts\activate.bat
  pip install -r requirements.txt pyinstaller
) else (
  call venv\Scripts\activate.bat
)

pyinstaller --noconfirm --clean --onefile --windowed --name "EasySlicer" ^
  --hidden-import=engine ^
  --hidden-import=store ^
  --hidden-import=themes ^
  main.py

echo OK: dist\EasySlicer.exe
