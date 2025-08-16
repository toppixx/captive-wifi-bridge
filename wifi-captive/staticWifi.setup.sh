#!/bin/bash

# Exit on errors
set -e

echo "[1] Updating system and installing packages..."
sudo apt update
sudo apt install -y hostapd dnsmasq iptables

echo "[2]]sh -c 'cat > /etc/dnsmasq.conf <<EOF
interface=wlan1
dhcp-range=192.168.42.10,192.168.42.50,12h
address=/router/192.168.42.1
EOF'"

echo "[3] Configuring IP forwarding..."
sudo sed -i '/^#net.ipv4.ip_forward=1/s/^#//' /etc/sysctl.conf
sudo sysctl -p

echo "[4] Saving iptables NAT rules..."
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables-save | sudo tee /etc/iptables.up.rules > /dev/null

echo "[5] Creating hostapd config..."
sudo bash -c 'cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan1
driver=nl80211
ssid=TeddyBox
hw_mode=g
channel=6
auth_algs=1
wpa=2
wpa_passphrase=YourStrongPassword
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
rsn_pairwise=CCMP
ignore_broadcast_ssid=0
ieee80211n=1
country_code=US
EOF'

echo "[6] Linking hostapd config..."
sudo sed -i '/^#DAEMON_CONF=/s|^#||' /etc/default/hostapd
sudo sed -i 's|DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "[7] Enabling services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "[8] Done! Reboot to start hotspot."
