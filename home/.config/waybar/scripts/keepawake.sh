#!/bin/bash
# waybar eye: visible only while the control-center keep-awake inhibitor is running
if pgrep -f "systemd-inhibit.*SwayNC" >/dev/null; then
    echo '{"text":"󰈈","class":"on","alt":"on"}'
else
    echo '{"text":"","class":"off","alt":"off"}'
fi
