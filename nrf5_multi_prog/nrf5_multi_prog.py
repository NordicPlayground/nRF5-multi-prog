import argparse
from intelhex import IntelHex
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
import os
import sys

from pynrfjprog import MultiAPI as API


# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen


class CLI(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Program multiple nRF5 devices concurrently with this nrfjprog inspired python module/exe', epilog='https://github.com/NordicSemiconductor/nRF5-multi-prog')
        self.subparsers = self.parser.add_subparsers(dest='command')
        self.args = None

        self._add_recover_command()
        self._add_program_command()

    def run(self):
        return self.parser.parse_args()

    # Top level commands.

    def _add_recover_command(self):
        erase_parser = self.subparsers.add_parser('recover', help='Erase all user FLASH including UICR and disables any enabled readback protection/locking.')

        self._add_family_argument(erase_parser)
        self._add_snrs_argument(erase_parser)

    def _add_program_command(self):
        program_parser = self.subparsers.add_parser('program', help='Programs the device.')

        self._add_erase_before_flash_group(program_parser)
        self._add_family_argument(program_parser)
        self._add_file_argument(program_parser)
        self._add_reset_group(program_parser)
        self._add_snrs_argument(program_parser)
        self._add_verify_argument(program_parser)

    # Mutually exclusive groups of arguments.

    def _add_erase_before_flash_group(self, parser):
        erase_before_flash_group = parser.add_mutually_exclusive_group()
        self._add_eraseall_argument(erase_before_flash_group)
        self._add_sectors_erase_argument(erase_before_flash_group)
        self._add_sectorsuicr_erase_argument(erase_before_flash_group)

    def _add_reset_group(self, parser): # TODO: add other reset options.
        reset_group = parser.add_mutually_exclusive_group()
        self._add_sysreset_argument(reset_group)

    # Arguments.

    def _add_eraseall_argument(self, parser):
        parser.add_argument('-e', '--eraseall', action='store_true', help='Erase all user FLASH including UICR.')

    def _add_family_argument(self, parser):
        parser.add_argument('--family', type=str, help='The family of the target device. Defaults to NRF51.', required=False, choices=['NRF51', 'NRF52'])

    def _add_file_argument(self, parser):
        parser.add_argument('-f', '--file', help='The hex file to be programmed to all devices.', required=True)

    def _add_sectors_erase_argument(self, parser):
        parser.add_argument('-se', '--sectorserase', action='store_true', help='Erase all sectors that FILE contains data in before programming.')

    def _add_sectorsuicr_erase_argument(self, parser):
        parser.add_argument('-u', '--sectorsanduicrerase', action='store_true', help='Erase all sectors that FILE contains data in and the UICR (unconditionally) before programming.')

    def _add_snrs_argument(self, parser):
        parser.add_argument('-s', '--snrs', type=int, nargs='+', help='Selects the debuggers with the given serial numbers among all those connected to the PC for the operation. Defaults to all snrs with be selected.')

    def _add_sysreset_argument(self, parser):
        parser.add_argument('-r', '--systemreset', action='store_true', help='Executes a system reset.')

    def _add_verify_argument(self, parser):
        parser.add_argument('-v', '--verify', action='store_true', help='Read back memory and verify that it matches FILE.')


class nRF5MultiFlash(object):
    def __init__(self, args):
        self.nRF5_instances = {}
        self.args = args

        self.family = args.family
        self.snrs = args.snrs

        if not self.args.family:
            self.family = 'NRF51'

        if not self.args.snrs:
            with API.MultiAPI('NRF51') as nrf:
                self.snrs = nrf.enum_emu_snr()

        if self.family == 'NRF51':
            self.PAGE_SIZE = 0x400
        else:
            self.PAGE_SIZE = 0x1000

        if args.command == 'program':
            self.hex_file = IntelHex(self.file)

    def _byte_lists_equal(self, data, read_data):
        for i in xrange(len(data)):
            if data[i] != read_data[i]:
                return False
        return True

    def _connect_to_device(self, device):
        self.nRF5_instances[device] = API.MultiAPI(self.family)
        self.nRF5_instances[device].open()
        self.nRF5_instances[device].connect_to_emu_with_snr(device)

    def _recover_device(self, device):
        self.nRF5_instances[device].recover()

    def _program_device(self, device):
        if self.args.erase_all:
            self.nRF5_instances[device].erase_all()
        if self.args.sectors_and_uicr_erase:
            self.nRF5_instances[device].erase_uicr()

        for segment in self.hex_file.segments():
            start_addr, end_addr = segment
            size = end_addr - start_addr

            if self.args.sectors_erase or self.args.sectors_and_uicr_erase:
                start_page = int(start_addr / self.PAGE_SIZE)
                end_page = int(end_addr / self.PAGE_SIZE)
                for page in range(start_page, end_page + 1):
                    self.nRF5_instances[device].erase_page(page * self.PAGE_SIZE)

            data = self.hex_file.tobinarray(start=start_addr, size=(size)) # TODO: this can be optimized.
            self.nRF5_instances[device].write(start_addr, data.tolist(), True)

            if self.args.verify:
                read_data = self.nRF5_instances[device].read(start_addr, len(data))
                assert (self._byte_lists_equal(data, read_data)), 'Verify failed. Data readback from memory does not match data written.'

        if self.args.systemreset:
            self.nRF5_instances[device].sys_reset()
            self.nRF5_instances[device].go()


    def _cleanup(self, device):
        self.nRF5_instances[device].disconnect_from_emu()
        self.nRF5_instances[device].close()

    # Public methods.

    def perform_command(self, device):
        self._connect_to_device(device)

        if self.args.command == 'recover':
            self._recover_device(device)
        elif self.args.command == 'program':
            self._program_device(device)

        self._cleanup(device)


def main():
    cli = CLI()
    args = cli.run()

    nRF = nRF5MultiFlash(args)

    pool = ThreadPool(len(nRF.snrs))
    pool.map(nRF.perform_command, nRF.snrs)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
