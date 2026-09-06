#!/bin/bash
# Disarm the dGPU PCIe bridge (GPP0 -> SWUS -> SWDS -> RX 6500M) as a wake source.
# Cause of "PM: hibernation: Wakeup event detected during hibernation, rolling back"
# and of spurious wakes from suspend on Ryzen laptops. Run with sudo.
set -e
echo "==> udev rule: disable wakeup on the dGPU bridge chain at boot"
cat > /etc/udev/rules.d/90-dgpu-no-wakeup.rules <<'RULE'
# GPP0 root port (00:01.1) and the Navi 24 PCIe switch (01:00.0 upstream, 02:00.0 downstream)
ACTION=="add", SUBSYSTEM=="pci", KERNEL=="0000:00:01.1", ATTR{power/wakeup}="disabled"
ACTION=="add", SUBSYSTEM=="pci", KERNEL=="0000:01:00.0", ATTR{power/wakeup}="disabled"
ACTION=="add", SUBSYSTEM=="pci", KERNEL=="0000:02:00.0", ATTR{power/wakeup}="disabled"
RULE
echo "==> applying now (no reboot needed)"
for d in 0000:00:01.1 0000:01:00.0 0000:02:00.0; do echo disabled > /sys/bus/pci/devices/$d/power/wakeup; done
grep -qE '^GPP0.*enabled' /proc/acpi/wakeup && echo GPP0 > /proc/acpi/wakeup || true
echo "==> state"
grep -E '^(GPP0|SWUS|SWDS)' /proc/acpi/wakeup
for d in 0000:00:01.1 0000:01:00.0 0000:02:00.0; do echo "$d wakeup=$(cat /sys/bus/pci/devices/$d/power/wakeup)"; done
echo "==> hibernate mode: fall back to 'shutdown' if 'platform' still rolls back"
echo "    (uncomment HibernateMode=shutdown in /etc/systemd/sleep.conf.d/hibernate.conf)"
grep -q HibernateMode /etc/systemd/sleep.conf.d/hibernate.conf || printf '#HibernateMode=shutdown\n' >> /etc/systemd/sleep.conf.d/hibernate.conf
echo "done"
