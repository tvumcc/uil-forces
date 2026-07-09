import os
import shutil

files = [
    "theme-monokai.js",
    "mode-java.js",
    "mode-python.js",
    "mode-c_cpp.js",
    "keybinding-vim.js"
]

os.makedirs("../backend/dist/ace-builds/src-noconflict", exist_ok=True)

for file in files:
    shutil.copyfile(os.path.join("node_modules/ace-builds/src-noconflict", file), os.path.join("../backend/dist/ace-builds/src-noconflict", file))