#!/bin/bash
# clipboard history picker (cliphist + rofi); Super+Shift+V
cliphist list | rofi -dmenu -display-columns 2 -p "clip" | cliphist decode | wl-copy
