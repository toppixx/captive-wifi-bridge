#!/bin/bash

IFACE="wlan1"
# CONF="/etc/hostapd/captive_portal.hostapd.conf"
CONF="/etc/hostapd/staticWifi.hostapd.conf"
LOG="/var/log/hostapd_watchdog.log"

echo "[$(date)] Starting hostapd watchdog..." >> "$LOG"

# Unblock Wi-Fi in case RF-kill was triggered
rfkill unblock wifi
sleep 1

# Make sure interface is up
ip link set "$IFACE" up

# Confirm it's not already in use
if iw "$IFACE" info | grep -q "type AP"; then
    echo "[$(date)] $IFACE already in AP mode" >> "$LOG"
else
    echo "[$(date)] Forcing $IFACE into AP mode..." >> "$LOG"
    iw dev "$IFACE" set type __ap
fi

# Infinite loop to keep hostapd alive
while true; do
    echo "[$(date)] Launching hostapd..." >> "$LOG"
    hostapd "$CONF"
    echo "[$(date)] hostapd exited! Restarting in 5 sec..." >> "$LOG"
    sleep 5
done
