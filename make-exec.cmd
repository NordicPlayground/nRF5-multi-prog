:: Name:     make-exec.cmd
:: Purpose:  Bundles source into a single exe.
::
:: Note:     See make-exec.sh for Linux/OS X.
::           This script assumes a Windows machine with git, 32-bit Python 2.7, 3.4 or 3.5, and pip installed.

@echo off
setlocal

set bin_dir=bin\
set bin_name=nRF5-multi-prog
set python_main=nrf5_multi_prog/nrf5_multi_prog.py

rem TODO: Check Python version, pip, and set up virtual environment.

echo pip installing python modules required by %python_main%...
pip install -r requirements.txt > NUL

echo pip installing pyinstaller...
pip install pyinstaller > NUL

if exist %bin_dir% rm -rf %bin_dir%

echo bundling %python_main% as %bin_name%.exe using pyinstaller...
pyinstaller -F %python_main% --name %bin_name% --log-level ERROR --clean

echo moving %bin_name% to %bin_dir%...
mkdir %bin_dir%
mv dist\%bin_name%.exe %bin_dir%
