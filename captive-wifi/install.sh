#!/bin/bash    
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi


managed_wifi="tc_wifi_manager"
static_wifi="static_wifi"

echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y hostapd dnsmasq python3-venv python3-pip

echo "📁 Setting up project directory..."
mkdir -p /home/pi/$managed_wifi

echo "📄 Creating hostapd config for the captive config hotspot..."
sudo cp captive_portal.dnsmasq.conf /etc/captive_portal.dnsmasq.conf
sudo cp captive_portal.hostapd.conf /etc/hostapd/captive_portal.hostapd.conf

echo "📄 Creating hostapd config for the static hotspot..."
sudo cp staticWifi.dnsmasq.conf /etc/staticWifi.dnsmasq.conf
sudo cp staticWifi.hostapd.conf /etc/hostapd/staticWifi.hostapd.conf

echo "📶 enabling wifis"
sudo rfkill unblock wifi
sudo systemctl enable hostapd
sudo systemctl restart hostapd
sudo ip link set wlan0 up
sudo ip link set wlan1 up
sudo nmcli radio wifi on

sudo cp captive_portal_manager.py /home/pi/$managed_wifi
sudo cp captive_portal.py /home/pi/$managed_wifi
sudo cp -r static /home/pi/$managed_wifi/static
sudo cp -r templates /home/pi/$managed_wifi/templates

cd /home/pi/$managed_wifi

echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "🐍 Installing Python packages inside virtualenv..."
venv/bin/pip install flask
venv/bin/pip install gunicorn


echo "📄 Creating SSL certificates... this could take some time"
if [ -f "cert.pem" ]; then
  echo "cert.pem already created."
else
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=DE/ST=Bavaria/L=Bad Toelz/O=NoCompany/OU=Hobby/CN=tc"
fi
if [ -f "key.pem" ]; then
  echo "key.pem already created."
else
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=DE/ST=Bavaria/L=Bad Toelz/O=NoCompany/OU=Hobby/CN=tc"
fi

# echo "📄 Placing WiFi Manager daemon..."
# cat > $managed_wifi.py << 'EOF'
# # >>> Paste your full $managed_wifi.py content here <<<
# EOF

# echo "📄 Placing Captive Portal script..."
# cat > captive_portal.py << 'EOF'
# # >>> Paste your full captive_portal.py content here <<<
# EOF

# sudo tee /etc/hostapd/hostapd2.conf > /dev/null << 'EOF'
# interface=wlan1
# driver=nl80211
# ssid=SetupPortal
# hw_mode=g
# channel=1
# auth_algs=1
# wmm_enabled=0
# EOF

# echo "📄 Creating dnsmasq config for captive portal..."
# sudo tee /etc/dnsmasq2.conf > /dev/null << 'EOF'
# interface=wlan1
# dhcp-range=192.168.50.2,192.168.50.50,12h
# address=/#/192.168.50.1
# EOF

echo "🔧 Creating systemd service for WiFi manager..."
sudo tee /etc/systemd/system/$managed_wifi.service > /dev/null << EOF
[Unit]
Description=WiFi Management Daemon with Virtualenv
After=network.target

[Service]
ExecStart=/home/pi/$managed_wifi/venv/bin/python /home/pi/$managed_wifi/captive_portal_manager.py
Restart=always
User=root
WorkingDirectory=/home/pi/$managed_wifi

[Install]
WantedBy=multi-user.target
EOF

echo "🔧 Creating systemd service for static WiFi..."
sudo tee /etc/systemd/system/$static_wifi.service > /dev/null << EOF
[Unit]
Description=hostapd AP (custom config)
After=network.target

[Service]
Type=simple
User=root
ExecStartPre=/usr/sbin/ip link set wlan1 down
ExecStartPre=/usr/sbin/ip link set wlan1 up
ExecStart=/usr/sbin/hostapd /etc/hostapd/staticWifi.hostapd.conf
Restart=on-failure
WorkingDirectory=/home/pi/$managed_wifi

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reloading systemd and enabling WiFi manager service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $managed_wifi.service
sudo systemctl start $managed_wifi.service
sudo systemctl enable $static_wifi.service
sudo systemctl start $static_wifi.service

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -w net.ipv4.ip_forward=1

# Set up iptables for NAT
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE
sudo iptables -A FORWARD -i wlan1 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT

# Save iptables rules persistently
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

# Start dnsmasq using this config
sudo pkill dnsmasq
sudo dnsmasq --conf-file=/etc/staticWifi.dnsmasq.conf
# sudo dnsmasq --conf-file=/etc/captive_portal.dnsmasq.conf

echo "✅ Installation complete!"
echo "🧠 Your Pi now auto-manages WiFi and launches a captive portal if needed."
