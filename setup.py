import os

from src.backend.orm import *
from src.backend.setup import *

setup_path = "setup"

if __name__ == "__main__":
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