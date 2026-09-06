#!/bin/bash
# Hibernation setup for a btrfs swapfile + rEFInd. Run with: sudo bash setup-hibernate.sh
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run with sudo"; exit 1; }
SWAP=/swap/swapfile
REFIND=/boot/refind_linux.conf
BK=~/setup_and_config/backup-2026-09-06

echo "==> checking swapfile"
[[ -f $SWAP ]] || { echo "no $SWAP"; exit 1; }
lsattr "$SWAP" | grep -q '^[^ ]*C' || { echo "swapfile is not nocow (chattr +C); hibernation would corrupt it. aborting."; exit 1; }
dev=$(findmnt -no SOURCE -T "$SWAP" | sed 's/\[.*//')
partuuid=$(blkid -s PARTUUID -o value "$dev")
offset=$(btrfs inspect-internal map-swapfile -r "$SWAP")
[[ -n $partuuid && $offset =~ ^[0-9]+$ ]] || { echo "could not determine partuuid/offset"; exit 1; }
echo "    device=$dev partuuid=$partuuid resume_offset=$offset"

echo "==> backing up"
mkdir -p "$BK"; cp -n "$REFIND" "$BK/refind_linux.conf.orig" 2>/dev/null || true
cp -n /etc/mkinitcpio.conf "$BK/mkinitcpio.conf.orig" 2>/dev/null || true

echo "==> mkinitcpio: adding resume hook"
if ! grep -qE '^HOOKS=.*\bresume\b' /etc/mkinitcpio.conf; then
    sed -i -E 's/^(HOOKS=.*\bfilesystems\b)/\1 resume/' /etc/mkinitcpio.conf
fi
grep -E '^HOOKS' /etc/mkinitcpio.conf

echo "==> rEFInd: adding resume= to kernel options"
if ! grep -q 'resume=' "$REFIND"; then
    sed -i "s|rootflags=subvol=@|rootflags=subvol=@ resume=PARTUUID=$partuuid resume_offset=$offset|g" "$REFIND"
fi
grep -c 'resume=' "$REFIND" >/dev/null || { echo "failed to edit $REFIND"; exit 1; }
sed 's/^/    /' "$REFIND"

echo "==> systemd: lid closes to suspend-then-hibernate on battery"
mkdir -p /etc/systemd/logind.conf.d /etc/systemd/sleep.conf.d
cat > /etc/systemd/logind.conf.d/lid.conf <<'CONF'
[Login]
HandleLidSwitch=suspend-then-hibernate
HandleLidSwitchExternalPower=suspend
HandleLidSwitchDocked=ignore
CONF
cat > /etc/systemd/sleep.conf.d/hibernate.conf <<'CONF'
[Sleep]
# time asleep before suspend-then-hibernate converts to hibernate (systemd also
# wakes early on its own if the battery is estimated to run out sooner)
HibernateDelaySec=2h
CONF

echo "==> regenerating initramfs"
mkinitcpio -P

echo "==> cleaning partial pacman downloads"
rm -f /var/cache/pacman/pkg/download-*

echo
echo "done. reboot, then verify with:"
echo "  cat /sys/power/resume /sys/power/resume_offset   # should not be 0:0 / 0"
echo "  systemctl hibernate                              # first real test, with work saved"
