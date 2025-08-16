#!/bin/bash

set -e

TC_HOTSPOT="tc_hotspot"
TC_HOTSPOT_PASSWORD="password123"

TC_CAPTURE="tc_capture"
TC_CAPTURE_PASSWORD="12345678"

SSID="MyBridgeHotspot"
UPSTREAM_SSID="Rabbit Hole"
UPSTREAM_PASSWORD="6kozzzAPQXa!YEfy"

echo "📡 Setting up bridged Wi-Fi hotspot..."
echo "Disable hostapd and dnsmasq. Only use nmcli Network Manager"
sudo systemctl mask hostapd
sudo systemctl disable hostapd
sudo systemctl mask dnsmasq
sudo systemctl disable dnsmasq


iptables -F
iptables -t nat -F

# Disable dhcpcd for wlan interfaces
echo "denyinterfaces wlan0 wlan1" | sudo tee -a /etc/dhcpcd.conf

# Create the bridge interface
# iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
# iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT
# iptables -A FORWARD -i wlan1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Remove the bridge interface
# iptables -t nat -D POSTROUTING -o wlan0 -j MASQUERADE
# iptables -D FORWARD -i wlan0 -o wlan1 -j ACCEPT
# iptables -D FORWARD -i wlan1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT

if echo $(nmcli --terse connection show) | grep -q "$TC_HOTSPOT"; then
   sudo nmcli connection delete $TC_HOTSPOT
else
    echo ""
fi

# nmcli con add type wifi ifname wlan0 con-name $TC_HOTSPOT autoconnect yes ssid $TC_HOTSPOT
# nmcli con modify $TC_HOTSPOT ipv4.addresses 192.168.88.1/24
# nmcli con modify $TC_HOTSPOT 802-11-wireless.band bg
# nmcli con modify $TC_HOTSPOT 802-11-wireless.channel 1
# nmcli con modify $TC_HOTSPOT ipv4.addresses 192.69.42.1/24
# nmcli con modify $TC_HOTSPOT 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
# nmcli con modify $TC_HOTSPOT wifi-sec.key-mgmt wpa-psk
# nmcli con modify $TC_HOTSPOT 802-11-wireless-security.proto rsn
# nmcli con modify $TC_HOTSPOT wifi-sec.psk "$TC_HOTSPOT_PASSWORD"

# nmcli con up $TC_HOTSPOT
# nmcli con down $TC_HOTSPOT


# Connect wlan1 to upstream using nmcli
# echo "🔌 Connecting wlan1 to upstream Wi-Fi..."
# nmcli device wifi connect "$UPSTREAM_SSID" password "$UPSTREAM_PASSWORD" ifname wlan1

if echo $(nmcli --terse connection show) | grep -q "$TC_CAPTURE"; then
   sudo nmcli connection delete $TC_CAPTURE
else
    echo ""
fi


nmcli con add type wifi ifname wlan1 con-name $TC_CAPTURE autoconnect yes ssid $TC_CAPTURE
# nmcli con modify $TC_CAPTURE 802-11-wireless.band bg
# nmcli con modify $TC_CAPTURE 802-11-wireless.channel 1
nmcli con modify $TC_CAPTURE ipv4.addresses 192.69.42.1/24
nmcli con modify $TC_CAPTURE 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
nmcli con modify $TC_CAPTURE wifi-sec.key-mgmt wpa-psk
nmcli con modify $TC_CAPTURE 802-11-wireless-security.proto rsn
nmcli con modify $TC_CAPTURE wifi-sec.psk "$TC_CAPTURE_PASSWORD"

nmcli con up $TC_CAPTURE


echo "✅ Setup complete! Reboot to activate bridged hotspot."
