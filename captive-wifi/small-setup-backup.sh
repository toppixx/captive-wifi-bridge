#!/bin/bash

set -e

TC_HOTSPOT="tc_hotspot"
TC_HOTSPOT_PASSWORD="password123"

SSID="MyBridgeHotspot"
PASSPHRASE="YourStrongPassword"
UPSTREAM_SSID="Rabbit Hole"
UPSTREAM_PASSWORD="6kozzzAPQXa!YEfy"

echo "📡 Setting up bridged Wi-Fi hotspot..."
echo "Disable hostapd and dnsmasq. Only use nmcli Network Manager"
sudo systemctl mask hostapd
sudo systemctl disable hostapd
sudo systemctl mask dnsmasq
sudo systemctl disable dnsmasq

sudo iptables -Fa
sudo iptables -t nat -F

sleep 2
# Disable dhcpcd for wlan interfaces
echo "denyinterfaces wlan0 wlan1" | sudo tee -a /etc/dhcpcd.conf

# Create the bridge interface
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT
iptables -A FORWARD -i wlan1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT

if echo $(nmcli --terse connection show) | grep -q "$TC_HOTSPOT"; then
   sudo nmcli connection delete $TC_HOTSPOT
else
    echo ""
fi

nmcli con add type wifi ifname wlan0 con-name $TC_HOTSPOT autoconnect yes ssid $TC_HOTSPOT
#nmcli con modify $TC_HOTSPOT ipv4.addresses 192.168.88.1/24
nmcli con modify $TC_HOTSPOT ipv4.addresses 192.69.42.1/24
nmcli con modify $TC_HOTSPOT 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
nmcli con modify $TC_HOTSPOT wifi-sec.key-mgmt wpa-psk
nmcli con modify $TC_HOTSPOT 802-11-wireless-security.proto rsn
nmcli con modify $TC_HOTSPOT wifi-sec.psk "$TC_HOTSPOT_PASSWORD"

nmcli con up $TC_HOTSPOT

# Connect wlan1 to upstream using nmcli
echo "🔌 Connecting wlan1 to upstream Wi-Fi..."
nmcli device wifi connect "$UPSTREAM_SSID" password "$UPSTREAM_PASSWORD" ifname wlan1

echo "✅ Setup complete! Reboot to activate bridged hotspot."
