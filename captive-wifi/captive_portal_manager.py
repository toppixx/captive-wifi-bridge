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

def is_connected():
    return False
    try:
        subprocess.check_call(["ping", "-c", "1", CHECK_HOST], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def start_hotspot():
    print("📡 Starting hotspot...")
    for cmd in HOTSPOT_SERVICES:
        subprocess.Popen(cmd.split())

def stop_hotspot():
    print("🛑 Stopping hotspot...")
    subprocess.call(["pkill", "-f", "hostapd"])
    subprocess.call(["pkill", "-f", "dnsmasq"])
    subprocess.call(["pkill", "-f", "captive_portal.py"])

def try_connect_known_wifi():
    print("🔍 Trying known WiFi...")
    os.system("wpa_cli reconfigure")
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
                start_hotspot()
        time.sleep(300)  # Repeat every 30 seconds

if __name__ == "__main__":
    main()
