from waitress import serve

import os

from tests.utils import print_binary_check, run_judge_self_test
from src.models.orm import *
from src.setup import *
from src.utils import *
from src.app import app, runtime_dir

def setup(setup_path = "setup"):
    if init_new_db():
        if not os.path.exists(setup_path):
            print(f"Setup directory './{setup_path}' does not exist!")
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
    # Automatically add Python and Java toolchains to PATH on Windows systems
    if IS_WINDOWS:
        python_toolchain_path = os.path.join(runtime_dir, "tools", "python")
        java_toolchain_path = os.path.join(runtime_dir, "tools", "java", "bin")

        if os.path.exists(python_toolchain_path):
            add_to_user_path(os.path.abspath(python_toolchain_path))
        if os.path.exists(java_toolchain_path):
            add_to_user_path(os.path.abspath(java_toolchain_path))

    print("UIL Forces Host")
    print("Possible actions:")
    print("1. Run server")
    print("2. Start server setup")
    print("3. Check required tools (Python interpreter and JDK on PATH)")
    print("4. Judge self-test")
    print("5. Quit")

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

                serve(app, host="0.0.0.0", port=5000, threads=10)
                terminating_action = True
        elif action == "2":
            setup()
        elif action == "3":
            print_binary_check()
        elif action == "4":
            run_judge_self_test()
        elif action == "5":
            terminating_action = True
        else:
            print("Invalid action.")