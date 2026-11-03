from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.clock import Clock
from kivy.animation import Animation
import threading
import queue
import os

# ==========================
#  Desktop Serial Bluetooth
# ==========================
try:
    import serial
    from serial import SerialException
except ImportError:
    serial = None
    class SerialException(Exception):
        pass


class SerialBluetoothManager:
    """Bluetooth через последовательный порт (macOS / Windows / Linux)."""

    def __init__(self, port="/dev/cu.HC-05", baudrate=9600, data_queue=None):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.queue = data_queue
        self._running = False
        self.read_thread = None

    def connect(self):
        if serial is None:
            print("[BT-Serial] pyserial not installed")
            return
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            print(f"[BT-Serial] Connected to {self.port}")
            self._running = True
            self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self.read_thread.start()
        except SerialException as e:
            print(f"[BT-Serial] Connection error: {e}")
            self.ser = None

    def send(self, data: str):
        if not self.ser or not self.ser.is_open:
            print("[BT-Serial] Not connected")
            return
        if not data.endswith("\n"):
            data += "\n"
        try:
            self.ser.write(data.encode("utf-8"))
            self.ser.flush()
        except Exception as e:
            print("[BT-Serial] Send error:", e)

    def _reader_loop(self):
        while self._running:
            line = self.read_nonblocking()
            if line and self.queue:
                self.queue.put(line)

    def read_nonblocking(self):
        # Desktop readline с timeout=0.05 → НЕ блокирует UI
        if not self.ser or not self.ser.is_open:
            return None
        try:
            line = self.ser.readline()
            if not line:
                return None
            return line.decode("utf-8", "ignore").strip()
        except Exception:
            return None

    def close(self):
        self._running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass


# ==========================
#  Android Bluetooth (SPP)
# ==========================
if platform == "android":
    from jnius import autoclass

    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    UUID = autoclass("java.util.UUID")

    class AndroidBluetoothManager:
        """
        Android Bluetooth SPP — чтение в отдельном потоке.
        """
        def __init__(self, mac_address: str, data_queue=None):
            self.mac_address = mac_address
            self.adapter = None
            self.socket = None
            self.in_stream = None
            self.out_stream = None

            self.queue = data_queue
            self.read_thread = None
            self._running = False

        def connect(self):
            # socket.connect() блокирующий -> делаем всё в фоновом потоке, чтобы UI не зависал
            threading.Thread(target=self._connect_and_read, daemon=True).start()

        def _connect_and_read(self):
            try:
                self.adapter = BluetoothAdapter.getDefaultAdapter()
                if not self.adapter.isEnabled():
                    print("[BT-Android] Bluetooth OFF")
                    return

                device = self.adapter.getRemoteDevice(self.mac_address)
                spp_uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
                self.socket = device.createRfcommSocketToServiceRecord(spp_uuid)

                print(f"[BT-Android] Connecting to {self.mac_address}...")
                self.socket.connect()

                self.in_stream = self.socket.getInputStream()
                self.out_stream = self.socket.getOutputStream()

                print("[BT-Android] Connected!")
                if self.queue:
                    self.queue.put("[connected]")

            except Exception as e:
                print("[BT-Android] Connection error:", e)
                self.socket = None
                if self.queue:
                    self.queue.put(f"[connection error] {e}")
                return

            # уже в фоновом потоке -> просто читаем
            self._running = True
            self._reader_loop()

        # == ПОТОК ЧТЕНИЯ ==
        def _reader_loop(self):
            print("[BT-Android] Reader thread started")

            buffer = bytearray()

            while self._running:
                try:
                    b = self.in_stream.read()  # блокирующий вызов — НО ЭТО ОТДЕЛЬНЫЙ ПОТОК
                    if b == -1:  # соединение закрыто
                        break

                    if b in (10, 13):  # \n \r
                        if buffer:
                            line = buffer.decode("utf-8", "ignore").strip()
                            if self.queue:
                                self.queue.put(line)
                            buffer = bytearray()
                    else:
                        buffer.append(b)

                except Exception as e:
                    print("[BT-Android] Read error:", e)
                    break

            print("[BT-Android] Reader thread stopped")

        # == SEND ==
        def send(self, data: str):
            if not self.out_stream:
                print("[BT-Android] Not connected")
                return
            if not data.endswith("\n"):
                data += "\n"
            try:
                self.out_stream.write(data.encode("utf-8"))
                self.out_stream.flush()
            except Exception as e:
                print("[BT-Android] Send error:", e)

        # == CLOSE ==
        def close(self):
            self._running = False
            try:
                if self.in_stream:
                    self.in_stream.close()
                if self.out_stream:
                    self.out_stream.close()
                if self.socket:
                    self.socket.close()
                print("[BT-Android] Closed")
            except Exception:
                pass


# ==========================
#        DroneUI App
# ==========================

class DroneUI(App):
    pid_value = StringProperty("")
    terminal_text = StringProperty("")
    bt = None

    def build(self):
        # очередь для потокобезопасного обмена
        self.bt_queue = queue.Queue()

        # JsonStore
        self.store = JsonStore(os.path.join(self.user_data_dir, "settings.json"))
        if self.store.exists("pid"):
            self.pid_value = self.store.get("pid")["value"]

        # === Bluetooth ===
        if platform == "android":
            from android.permissions import request_permissions, Permission
            mac = "98:D3:02:96:9D:11"
            print("[APP] Using AndroidBluetoothManager")
            self.bt = AndroidBluetoothManager(mac, data_queue=self.bt_queue)

            def on_permissions(permissions, grants):
                # подключаемся только когда пользователь ответил на запрос разрешений
                if all(grants):
                    self.bt.connect()
                else:
                    self.bt_queue.put("[no bluetooth permission]")

            request_permissions([
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION
            ], on_permissions)

        else:
            print("[APP] Using SerialBluetoothManager")
            self.bt = SerialBluetoothManager("/dev/cu.HC-05", 9600, data_queue=self.bt_queue)
            self.bt.connect()

        # обновление UI
        Clock.schedule_interval(self.update_terminal, 0.1)

        return Builder.load_file("ui.kv")

    # == UI обновление ==
    def update_terminal(self, dt):
        while not self.bt_queue.empty():
            line = self.bt_queue.get()

            print("[BT]", line)

            self.terminal_text += "\n" + line
            self.terminal_text = "\n".join(self.terminal_text.splitlines()[-10:])

    # == Команды ==
    def send_command(self, cmd):
        if self.bt:
            self.bt.send(cmd)

    def up(self): self.send_command("Q")
    def down(self): self.send_command("E")
    def forward(self): self.send_command("W")
    def backward(self): self.send_command("S")
    def left(self): self.send_command("A")
    def right(self): self.send_command("D")
    def yaw_left(self): self.send_command("L")
    def yaw_right(self): self.send_command("R")

    # == ON/OFF (TODO: отправлять команду на Arduino, когда определишься с протоколом) ==
    count_on_off = 0

    def on_off(self, button):
        if self.count_on_off == 0:
            self.count_on_off = 1
            button.text = "ON"
            button.btn_color = (0, 0.7, 0, 1)
        else:
            self.count_on_off = 0
            button.text = "OFF"
            button.btn_color = (0.7, 0, 0, 1)

    # == PID ==
    def save_pid(self, text):
        self.pid_value = text
        self.store.put("pid", value=text)

    # == Панели меню ==
    def side_panel(self):
        panel = self.root.ids.side_panel
        if panel.x >= self.root.width:
            Animation(x=self.root.width - panel.width, d=0.25).start(panel)
        else:
            Animation(x=self.root.width, d=0.25).start(panel)

    def info_panel(self):
        info_panel = self.root.ids.info_panel
        side_panel = self.root.ids.side_panel
        if info_panel.x >= self.root.width:
            Animation(x=self.root.width - info_panel.width, d=0.25).start(info_panel)
        if side_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(side_panel)

    def contact_panel(self):
        contact_panel = self.root.ids.contact_panel
        side_panel = self.root.ids.side_panel
        if contact_panel.x >= self.root.width:
            Animation(x=self.root.width - contact_panel.width, d=0.25).start(contact_panel)
        if side_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(side_panel)

    def back_button(self):
        info_panel = self.root.ids.info_panel
        side_panel = self.root.ids.side_panel
        contact_panel = self.root.ids.contact_panel
        if contact_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(contact_panel)
        if info_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(info_panel)
        if side_panel.x >= self.root.width:
            Animation(x=self.root.width - side_panel.width, d=0.25).start(side_panel)

    def on_stop(self):
        if self.bt:
            self.bt.close()


if __name__ == "__main__":
    DroneUI().run()
