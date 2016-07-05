"""

"""
import argparse
from intelhex import IntelHex
from multiprocessing.dummy import Pool as ThreadPool

from pynrfjprog import MultiAPI as API

PAGE_SIZE = 0x100 # TODO: This is only nRF51


class CLI(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='description', epilog='epilog')
        self.subparsers = self.parser.add_subparsers(dest='command')
        self._add_program_command()

    def run(self):
        return self.parser.parse_args()

    # Top level commands.

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

    def _add_reset_group(self, parser):
        reset_group = parser.add_mutually_exclusive_group()
        self._add_sysreset_argument(reset_group)

    # Arguments.

    def _add_eraseall_argument(self, parser):
        parser.add_argument('-e', '--eraseall', action='store_true', help='Erase all user FLASH including UICR and disable any protection (this is actually recover()).')

    def _add_family_argument(self, parser):
        parser.add_argument('--family', type=str, help='The family of the target device.', required=False, choices=['NRF51', 'NRF52'])

    def _add_file_argument(self, parser):
        parser.add_argument('-f', '--file', help='The hex file to be used in this operation.', required=True)

    def _add_sectors_erase_argument(self, parser):
        parser.add_argument('-se', '--sectorserase', action='store_true', help='Erase all sectors that FILE contains data in before programming.')

    def _add_sectorsuicr_erase_argument(self, parser):
        parser.add_argument('-u', '--sectorsanduicrerase', action='store_true', help='Erase all sectors that FILE contains data in and the UICR (unconditionally) before programming.')

    def _add_snrs_argument(self, parser):
        parser.add_argument('-s', '--snrs', type=int, nargs='+', help='Selects the debuggers with the given serial numbers among all those connected to the PC for the operation.')

    def _add_sysreset_argument(self, parser):
        parser.add_argument('-r', '--systemreset', action='store_true', help='Executes a system reset.')

    def _add_verify_argument(self, parser):
        parser.add_argument('-v', '--verify', action='store_true', help='Read back memory and verify that it matches FILE.')


class nRF5MultiFlash(object):
    def __init__(self, args):
        self.nRF5_instances = {}
        self.erase_all = args.eraseall
        self.family = args.family
        self.file = args.file # 'test\\resources\\s110_softdevice.hex'
        self.sectors_erase = args.sectorserase
        self.sectors_and_uicr_erase = args.sectorsanduicrerase
        self.snrs = args.snrs
        self.systemreset = args.systemreset
        self.verify = args.verify

    def byte_lists_equal(self, data, read_data):
        for i in xrange(len(data)):
            if data[i] != read_data[i]:
                return False
        return True

    def connect_to_devices(self):
        tmp = API.MultiAPI('NRF51')
        tmp.open()

        if not self.family:
            self.family = 'NRF51'
        if not self.snrs:
            self.snrs = tmp.enum_emu_snr()

        for device in self.snrs:
            self.nRF5_instances[device] = API.MultiAPI(self.family)
            self.nRF5_instances[device].open()
            self.nRF5_instances[device].connect_to_emu_with_snr(device)

        tmp.close()

    def program_device(self, device):
        if self.erase_all:
            self.nRF5_instances[device].recover()
        if self.sectors_and_uicr_erase:
            self.nRF5_instances[device].erase_uicr()

        hex_file = IntelHex(self.file)
        for segment in hex_file.segments():
            start_addr, end_addr = segment
            size = end_addr - start_addr

            if self.sectors_erase or self.sectors_and_uicr_erase:
                start_page = int(start_addr / PAGE_SIZE)
                end_page = int(end_addr / PAGE_SIZE)
                for page in range(start_page, end_page + 1):
                    self.nRF5_instances[device].erase_page(page * PAGE_SIZE)

            data = hex_file.tobinarray(start=start_addr, size=(size))
            self.nRF5_instances[device].write(start_addr, data.tolist(), True)

            if self.verify:
                read_data = self.nRF5_instances[device].read(start_addr, len(data))
                assert (self.byte_lists_equal(data, read_data)), 'Verify failed. Data readback from memory does not match data written.'

            if self.systemreset:
                self.nRF5_instances[device].sys_reset()

def main():
    cli = CLI()
    args = cli.run()

    nRF = nRF5MultiFlash(args)
    nRF.connect_to_devices()
    pool = ThreadPool(4)
    results = pool.map(nRF.program_device, nRF.snrs)
    print(nRF.snrs)

if __name__ == '__main__':
    main()
