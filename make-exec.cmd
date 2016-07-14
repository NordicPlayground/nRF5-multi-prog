@echo off

REM Assumes we are running this script on Windows.

SET bin_dir=bin\
SET bin_name=nRF5-multi-prog
SET python_main=nrf5_multi_prog/nrf5_multi_prog.py

REM TODO: Check Python version, pip, and set up virtual environment.

echo pip installing python modules required by %python_main%...
pip install -r requirements.txt > NUL

echo pip installing pyinstaller...
pip install pyinstaller > NUL

IF EXIST %bin_dir% rm -rf %bin_dir%

echo bundling %python_main% as %bin_name%.exe using pyinstaller...
pyinstaller -F %python_main% --name %bin_name% --log-level ERROR --clean

echo moving %bin_name% to %bin_dir%...
mkdir %bin_dir%
mv dist\%bin_name%.exe %bin_dir%
