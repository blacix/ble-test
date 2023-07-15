from time import sleep
from threading import Thread
from queue import Queue
from queue import Empty

from bluezero import central
from bluezero import tools
from bluezero import constants
from bluezero import observer
from bluezero import adapter
import dbus.exceptions


# Phone Bluetooth UART RX UUID/Characteristic: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
# Phone Bluetooth UART TX UUID/Characteristic: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
# Control Box UART RX UUID/Characteristic: 00001525-1212-EFDE-1523-785FEABCD123
# Control Box UART TX UUID/Characteristic: 00001524-1212-EFDE-1523-785FEABCD123

BLE_MAC_ADDRESS = "88:88:88:88"

class BleCentral(Thread):
    CTRL_UART_SERVICE_UUID = 'b3e668c0-cf93-11ec-9d64-0242ac120002'
    PHONE_UART_SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
    CTRL_TX_CHARACTERISTIC_UUID = 'b3e668c1-cf93-11ec-9d64-0242ac120002'
    CTRL_RX_CHARACTERISTIC_UUID = 'b3e668c2-cf93-11ec-9d64-0242ac120002'
    PHONE_TX_CHARACTERISTIC_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
    PHONE_RX_CHARACTERISTIC_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'

    def __init__(self, device_addr, adapter_addr=None, **kwargs):
        super().__init__()
        self.phoneRxQueue = Queue()
        self.ctrlRxQueue = Queue()
        dongle = adapter.Adapter(adapter_addr)
        dongle.on_device_found = 
        dongle.start_discovery()
        self.bleCentral = central.Central(adapter_addr=adapter_addr, device_addr=device_addr)

        self._CtrlTxChar = self.bleCentral.add_characteristic(self.CTRL_UART_SERVICE_UUID,
                                                              self.CTRL_TX_CHARACTERISTIC_UUID)
        self._CtrlRxChar = self.bleCentral.add_characteristic(self.CTRL_UART_SERVICE_UUID,
                                                              self.CTRL_RX_CHARACTERISTIC_UUID)
        self._PhoneTxChar = self.bleCentral.add_characteristic(self.PHONE_UART_SERVICE_UUID,
                                                               self.PHONE_TX_CHARACTERISTIC_UUID)
        self._PhoneRxChar = self.bleCentral.add_characteristic(self.PHONE_UART_SERVICE_UUID,
                                                               self.PHONE_RX_CHARACTERISTIC_UUID)

    def connect(self):
        self.bleCentral.connect()
        self._CtrlRxChar.add_characteristic_cb(self._uart_ctrl_rx_callback)
        self._PhoneRxChar.add_characteristic_cb(self._uart_phone_rx_callback)
        self._CtrlRxChar.start_notify()
        self._PhoneRxChar.start_notify()

    def disconnect(self):
        self.bleCentral.disconnect()

    def isConnected(self):
        return self.bleCentral.connected

    def run(self):
        self.bleCentral.run()

    def quit(self):
        # Stop event loop
        self.bleCentral.quit()

    def _uart_ctrl_rx_callback(self, *pin_values):
        if 'Value' in pin_values[1]:
            self.ctrlRxQueue.put(bytes(pin_values[1]['Value']).decode('utf-8'))
            # print(bytes(pin_values[1]['Value']).decode('utf-8'))

    def _uart_phone_rx_callback(self, *pin_values):
        if 'Value' in pin_values[1]:
            self.phoneRxQueue.put(bytes(pin_values[1]['Value']).decode('utf-8'))

    def phoneTx(self, data):
        with self.phoneRxQueue.mutex:
            self.phoneRxQueue.queue.clear()
        # DBus exceptions are not handled in the library
        try:
            self._PhoneTxChar.write_value(data)
        except dbus.exceptions.DBusException as e:
            print(e)

    def ctrlTx(self, data):
        self._CtrlTxChar.write_value(data)

    def phoneReceive(self, timeout=5):
        try:
            return self.phoneRxQueue.get(True, timeout)
        except Empty as error:
            return None

    def ctrlReceive(self, timeout=5):
        try:
            return self.ctrlRxQueue.get(True, timeout)
        except Empty as error:
            return None


if __name__ == '__main__':
    bleCentral = BleCentral(BLE_MAC_ADDRESS)
    bleCentral.start()
    bleCentral.connect()

    sleep(1)
    bleCentral.phoneTx(b'act\n')

    item = bleCentral.phoneReceive(2)
    while item is not None:
        print(item)
        item = bleCentral.phoneReceive(2)

    bleCentral.disconnect()
    bleCentral.quit()
    bleCentral.join()
