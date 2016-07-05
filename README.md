nRF5-multi-prog
=========

Program multiple nRF5 devices concurrently with this nrfjprog inspired python module/exe. This is useful when programming multiple devices with the same hex file, greatly reducing the time it takes. Program n devices in roughly the same time it takes to program 1 device (usb limitation of around ~100 devices at once).

## Installation

  `pip install nrf5-multi-prog`  
  Or download a precompiled .exe from releases.

## Usage

  To see possible arguments: >nrf5-multi-prog program -h  
  
  >nrf5-multi-prog program --file PATH_TO_FILE --eraseall --verify --systemreset --snrs XXXXXXXXX YYYYYYYYY ZZZZZZZZZ ...  
  
  or from Python...  
  >python nrf5-multi-prog program.py --file ...  
  
  Note: The only required argument is --file which provides a path to the .hex file to be programmed to the device(s). If --snrs is not specified, all devices connected to the PC will be programmed with the .hex file. If --family is not specified, default family is NRF51.
  
  
