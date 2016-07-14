@echo off

REM Assumes we are running this script on Windows.

SET bin_dir=bin\
SET bin_name=nRF5-multi-prog
SET python_main=nrf5_multi_prog/nrf5_multi_prog.py

REM TODO: Check Python version, pip, and set up virtual environment.

pip install -r requirements.txt
pip install pyinstaller

IF EXIST %bin_dir% rm -rf %bin_dir%

pyinstaller -F %python_main% --name %bin_name% --log-level ERROR --clean

mkdir %bin_dir%
mv dist\%bin_name%.exe %bin_dir%
