import os
import time
import subprocess
print("✈ starting script")
WLAN_INTERFACE = "wlan0"
CHECK_HOST = "8.8.8.8"  # Google DNS for connectivity check
FLASK_CMD = "sudo /home/pi/tc_wifi_manager/venv/bin/gunicorn --bind 0.0.0.0:80 captive_portal:app"
HOSTAPD_CMD = "sudo hostapd /etc/hostapd/captive_portal.hostapd.conf"


# DNSMASQ_CMD = "dnsmasq --conf-file=/etc/captive_portal.dnsmasq.conf"
HOTSPOT_SERVICES = [HOSTAPD_CMD, FLASK_CMD]
def run(cmd, shell=False, printToConsole=True):
    if printToConsole:
      print(f"\n▶️  Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.run(cmd, shell=shell, check=True)

def is_connected():
    return False
    try:
        subprocess.check_call(["ping", "-c", "1", CHECK_HOST], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def start_hotspot(ssid, password):
    print("📡 Starting hotspot...")

    # Delete old hotspot connection if exists
    try:
        result = subprocess.run(["nmcli", "--terse", "connection", "show"],
                                capture_output=True, text=True, check=True)
        if ssid in result.stdout:
            run(["sudo", "nmcli", "connection", "delete", ssid])
    except subprocess.CalledProcessError:
        print("⚠️ Failed to list connections")


    # Add new hotspot
    run(["nmcli", "con", "add", "type", "wifi", "ifname", "wlan0", "con-name", ssid, "autoconnect", "yes", "ssid", ssid])
    run(["nmcli", "con", "modify", ssid, "ipv4.addresses", "192.69.42.1/24"])
    run(["nmcli", "con", "modify", ssid, "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg", "ipv4.method", "shared"])
    run(["nmcli", "con", "modify", ssid, "wifi-sec.key-mgmt", "wpa-psk"])
    run(["nmcli", "con", "modify", ssid, "802-11-wireless-security.proto", "rsn"])
    run(["nmcli", "con", "modify", ssid, "wifi-sec.psk", password], False, False)
    print("\n▶️  Running: " + " ".join(["nmcli", "con", "modify", ssid, "wifi-sec.psk", "*******",]))

    run(["ip", "link", "set", "wlan0", "up"])

    run(["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--dport", "80", "-j", "DNAT", "--to-destination", "192.69.42.1:80"])
    run(["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--dport", "443", "-j", "DNAT", "--to-destination", "192.69.42.1:80"])
    run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-j", "MASQUERADE"])

    subprocess.Popen(FLASK_CMD.split())

def stop_hotspot(stopSelf=True):
    print("🛑 Stopping hotspot...")
    subprocess.run(["pkill", "-f", "hostapd"], check=False)
    subprocess.run(["pkill", "-f", "dnsmasq"], check=False)
    if stopSelf:
      subprocess.run(["pkill", "-f", "captive_portal.py"], check=False)
    subprocess.run(["pkill", "wpa_supplicant"], check=False)
    subprocess.run(["pkill", "hostapd"], check=False)
    subprocess.run(["rm", "-f", "/run/wpa_supplicant/*"], check=False)
    subprocess.run(["rfkill", "unblock", "wlan"], check=False)
    subprocess.run(["ip", "link", "set", "wlan0", "down"], check=False)
    subprocess.run(["iptables", "-t", "nat", "-F"], check=False)
    subprocess.run(["iptables", "-t", "nat", "-D", "PREROUTING", "-p", "tcp", "--dport", "80", "-j", "DNAT", "--to-destination", "192.69.42.1:80"], check=False)
    subprocess.run(["iptables", "-t", "nat", "-D", "PREROUTING", "-p", "tcp", "--dport", "443", "-j", "DNAT", "--to-destination", "192.69.42.1:80"], check=False)
    subprocess.run(["iptables", "-t", "nat", "-D", "POSTROUTING", "-j", "MASQUERADE"], check=False)
    subprocess.run(["sudo", "iptables", "-t", "nat", "-D", "POSTROUTING", "-o", "wlan0", "-j", "MASQUERADE"], check=False)
    subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-i", "wlan0", "-o", "wlan1", "-j", "ACCEPT"], check=False)
    subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-i", "wlan1", "-o", "wlan0", "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"], check=False)

def try_connect_known_wifi():
    print("🔍 Trying known WiFi...")
    # os.system("wpa_cli reconfigure")
    time.sleep(10)  # Give it some time to connect

def main():
    while True:
        if is_connected():
            print("✅ Connected to WiFi")
            stop_hotspot()
        else:
            print("🚫 No WiFi connection")
            try_connect_known_wifi()
            time.sleep(5)
            if not is_connected():
                stop_hotspot(False)
                start_hotspot("tc_captive", "password123")
        time.sleep(300)  # Repeat every 30 seconds

if __name__ == "__main__":
    main()
