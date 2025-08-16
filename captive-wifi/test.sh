
captive_ssid="Hostspot-2"
#1. ðŸ”Œ Set Up a Wi-Fi Access Point (optional Captiv wifi if no wifi found)
#Remove previos used wifi-configuraitons
if echo $(nmcli --terse connection show) | grep -q "$captive_ssid"; then
   sudo nmcli connection delete $captive_ssid
else
    echo not found
fi

sudo nmcli con add type wifi ifname wlan1 con-name $captive_ssid autoconnect yes ssid $captive_ssid
# sudo nmcli con modify $captive_ssid 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
# sudo nmcli con modify $captive_ssid wifi-sec.key-mgmt wpa-psk
# sudo nmcli con modify $captive_ssid wifi-sec.psk "password123"

nmcli connection modify $captive_ssid \
  802-11-wireless.mode ap \
  802-11-wireless.ssid $captive_ssid \
  802-11-wireless.band bg \
  802-11-wireless.channel 1 \
  802-11-wireless-security.proto rsn \
  802-11-wireless-security.key-mgmt wpa-psk \
  802-11-wireless-security.psk "MyStrongPass"
sudo nmcli con up $captive_ssid