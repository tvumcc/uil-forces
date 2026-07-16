from waitress import serve

import os

from src.models.orm import *
from src.setup import *
from src.utils import log, get_all_local_ips
from src.app import app

def setup(setup_path = "setup"):
    if init_new_db():
        if not os.path.exists(setup_path):
            print(f"Setup directory './{setup_path}' does not exist! Aborting...")
        else:
            import_from_directory(setup_path)
    else:
        merge = "merge"
        while merge.lower() not in ["", "y", "n"]:
            merge = input("Would like to merge the new setup config into the database? Nothing will be deleted, only added. (Y/n)")
            if merge.lower() in ["", "y"]:
                import_from_directory(setup_path)
            elif merge.lower() == "n":
                break 

if __name__ == "__main__":
    print("UIL Forces")
    print("Possible actions:")
    print("1. Run server")
    print("2. Start server setup")
    print("3. Quit")

    terminating_action = False
    while not terminating_action:
        action = input("Please specify an action: ")
        if action == "1":
            if not os.path.exists("main.db"):
                print("A database does not yet exist for this instance. Select '2. Start server setup' to create it.")
            else:
                port = 5000
                ips = get_all_local_ips()
                print("Server started, access it at:")
                print(f"- Local:   http://127.0.0.1:{port}")
                if ips:
                    for ip in ips:
                        print(f"- Network: \x1b[1;4;33mhttp://{ip}:{port}\x1b[0m (Ctrl + Left Click to open)")
                else:
                    print("\t(No network interfaces detected)")

                serve(app, host="0.0.0.0", port=5000, threads=8)
                terminating_action = True
        elif action == "2":
            setup()
            print("Successfully completed setup.")
        elif action == "3":
            terminating_action = True
        else:
            print("Invalid action.")