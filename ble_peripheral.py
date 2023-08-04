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




def read_value():
    """
    :return: list of uint8 values
    """

    print('read_value callback')
    cpu_value = random.randrange(3200, 5310, 10) / 100
    # convert to 2 byte long int, and create a byte array from it
    return list(int(cpu_value * 100).to_bytes(2,
                                              byteorder='little', signed=True))


def write_callback(value: [int], options):
    print('write_callback')

def on_connect(local_address:device.Device=None, remote_address=None):
    print('on_connect', local_address, remote_address)

def on_disconnect(local_address=None, remote_address=None):
    print('on_disconnect', local_address, remote_address)


def update_value(characteristic):
    """
    Example of callback to send notifications

    :param characteristic:
    :return: boolean to indicate if timer should continue
    """
    # read/calculate new value.
    new_value = read_value()
    # Causes characteristic to be updated and send notification
    characteristic.set_value(new_value)
    # Return True to continue notifying. Return a False will stop notifications
    # Getting the value from the characteristic of if it is notifying
    return characteristic.is_notifying


def notify_callback(notifying, characteristic: localGATT.Characteristic):
    """
    called when notification enabled state changed
    """
    print('notify_callback', notifying)
    if notifying:
        async_tools.add_timer_seconds(1, update_value, characteristic)
    


def main(adapter_address):
    """Creation of peripheral"""
    logger = logging.getLogger('localGATT')
    logger.setLevel(logging.DEBUG)
    # Example of the output from read_value
    print('CPU temperature is {}\u00B0C'.format(
        int.from_bytes(read_value(), byteorder='little', signed=True)/100))
    # Create peripheral
    test_device_peripheral = peripheral.Peripheral(adapter_address, local_name='test device')
    test_device_peripheral.on_connect = on_connect
    test_device_peripheral.on_disconnect = on_disconnect
    # Add service
    test_device_peripheral.add_service(srv_id=1, uuid=UART_SERVICE, primary=True)
    # Add characteristic

    test_device_peripheral.add_characteristic(srv_id=1, chr_id=1, uuid=RX_CHARACTERISTIC,
                                value=[], notifying=False,
                                flags=['notify','write', 'write-without-response'],
                                write_callback=write_callback,
                                read_callback=read_value,
                                notify_callback=notify_callback)
    
    # test_device_peripheral.add_descriptor(srv_id=1, chr_id=1, dsc_id=1, uuid=RX_CHARACTERISTIC,
    #                            value=[0x0E, 0xFE, 0x2F, 0x27, 0x01, 0x00,
    #                                   0x00],
    #                            flags=['notify','write', 'write-without-response'])
    
    # test_device_peripheral.add_characteristic(srv_id=1, chr_id=2, uuid=TX_CHARACTERISTIC,
    #                             value=[], notifying=True,
    #                             flags=['notify'],
    #                             notify_callback=notify_callback,
    #                             read_callback=read_value,
    #                             write_callback=write_callback)

    test_device_peripheral.publish()

    


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
    # dongle.on_device_found = stuff
    # dongle.nearby_discovery()
    # dongle.powered = False

    main('84:7B:57:F6:AD:A0')
