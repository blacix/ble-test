"""Example of how to create a Peripheral device/GATT Server"""
# Standard modules
import logging
import random
from threading import Thread
import time

# Bluezero modules
from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral
from bluezero import device
from bluezero import localGATT

# constants
UART_SERVICE = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_CHARACTERISTIC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
TX_CHARACTERISTIC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
TEST_MESSAGE_SIZE = 2048


class PeripheralTest:
    def __init__(self) -> None:
        self.rx_buffer = []
        self.tx_buffer = []
        self.test_device_peripheral: peripheral.Peripheral = None
        self.rx_characteristic: localGATT.Characteristic = None
        self.tx_characteristic: localGATT.Characteristic = None
        self.rx_value: int = 0
        self.MTU = 20
        self.tx_str = ""
        for i in range(0, TEST_MESSAGE_SIZE - 1):
            self.tx_str += str(i % 10)
        self.tx_str += '\n'
        print(self.tx_str)

    def tx_read_value(self):
        """
        :return: list of uint8 values
        """
        print('tx_read_value callback')
        return self.tx_buffer

    def rx_write_callback(self, value: [], options):
        print('rx_write_callback, options: ', options)
        self.MTU = options['mtu'] - 5
        print('MTU: ', self.MTU)
        self.rx_buffer = value
        self.rx_value = int.from_bytes(self.rx_buffer, byteorder='big')
        print('rx_write_callback', self.rx_value)
        self.update_tx_value(self.tx_characteristic)

    def on_connect(self, local_address: device.Device = None, remote_address=None):
        print('on_connect', local_address, remote_address)

    def on_disconnect(self, local_address=None, remote_address=None):
        print('on_disconnect', local_address, remote_address)

    def update_tx_value(self, characteristic: localGATT.Characteristic):
        """
        callback to send notifications
        :param characteristic:
        :return: boolean to indicate if timer should continue
        """
        # Causes characteristic to be updated and send notification
        print('update_tx_value')
        self.rx_value = self.rx_value + 1
        self.tx_buffer = self.rx_value.to_bytes(4, byteorder='big')
        self.tx_buffer = bytearray(self.tx_str, 'utf-8')
        offset = 0
        tx_buffer_len = len(self.tx_buffer)
        while offset < tx_buffer_len:
            out = self.tx_buffer[offset:offset + self.MTU]
            print('chunk', out)
            characteristic.set_value(out)
            offset += self.MTU
        if offset < tx_buffer_len:
            out = self.tx_buffer[offset:]
            print('chunk', out)
            characteristic.set_value(out)

        # Return True to continue notifying. Return a False will stop notifications
        # Getting the value from the characteristic of if it is notifying
        return characteristic.is_notifying

    def tx_notify_callback(self, notifying, characteristic: localGATT.Characteristic):
        """
        called when notification enabled state changed
        """
        print('tx_notify_callback', notifying)
        if notifying:
            pass
            # self.update_tx_value(characteristic)
            # async_tools.add_timer_seconds(1, self.update_value, characteristic)

    def main(self, adapter_address):
        """Creation of peripheral"""
        logger = logging.getLogger('localGATT')
        logger.setLevel(logging.DEBUG)

        # Create peripheral
        self.test_device_peripheral = peripheral.Peripheral(adapter_address, local_name='test device')
        self.test_device_peripheral.on_connect = self.on_connect
        self.test_device_peripheral.on_disconnect = self.on_disconnect
        # Add service
        self.test_device_peripheral.add_service(srv_id=1, uuid=UART_SERVICE, primary=True)
        # Add characteristic
        self.rx_characteristic = localGATT.Characteristic(service_id=1, characteristic_id=1, uuid=RX_CHARACTERISTIC,
                                                          value=[], notifying=False,
                                                          flags=['write'],
                                                          write_callback=self.rx_write_callback,
                                                          read_callback=None,
                                                          notify_callback=None)
        self.test_device_peripheral.characteristics.append(self.rx_characteristic)

        self.tx_characteristic = localGATT.Characteristic(service_id=1, characteristic_id=2, uuid=TX_CHARACTERISTIC,
                                                          value=[], notifying=False,
                                                          flags=['read', 'indicate'],
                                                          write_callback=None,
                                                          read_callback=self.tx_read_value,
                                                          notify_callback=self.tx_notify_callback)
        self.test_device_peripheral.characteristics.append(self.tx_characteristic)

        self.test_device_peripheral.publish()

    @staticmethod
    def print_device(device: device.Device):
        print(device.address)
        print(device.name)


if __name__ == '__main__':
    # # Get the default adapter address and pass it to main
    # main(list(adapter.Adapter.available())[0].address)

    dongles = adapter.list_adapters()
    print('dongles available: ', dongles)
    dongle = adapter.Adapter(dongles[0])

    print('address: ', dongle.address)
    print('name: ', dongle.name)
    print('alias: ', dongle.alias)
    print('powered: ', dongle.powered)
    print('pairable: ', dongle.pairable)
    print('pairable timeout: ', dongle.pairabletimeout)
    print('discoverable: ', dongle.discoverable)
    print('discoverable timeout: ', dongle.discoverabletimeout)
    print('discovering: ', dongle.discovering)
    print('Powered: ', dongle.powered)
    if not dongle.powered:
        dongle.powered = True
        print('Now powered: ', dongle.powered)
    # print('Start discovering')
    # dongle.on_device_found = PeripheralTest.stuff
    # dongle.nearby_discovery()
    # dongle.powered = False
    PeripheralTest().main('84:7B:57:F6:AD:A0')
