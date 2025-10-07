import os
import serial


class SerialCommunication:
    def __init__(self):
        port = os.getenv("SERIAL_PORT", "COM6")
        baud = int(os.getenv("SERIAL_BAUD", "115200"))
        try:
            self.com = serial.Serial(port, baud, write_timeout=10)
        except Exception as e:
            # Defer initialization; allow app to run without serial device
            self.com = None

    def sending_data(self, command: str) -> None:
        if self.com and self.com.is_open:
            self.com.write(command.encode('ascii'))
        else:
            # optional: log or ignore when serial not available
            pass

    def close(self):
        try:
            if self.com and self.com.is_open:
                self.com.close()
        except Exception:
            pass
