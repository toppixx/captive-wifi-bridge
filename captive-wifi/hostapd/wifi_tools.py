import subprocess
import time
import os

def create_wpa_config(ssid: str, psk: str) -> str:
    return f"""\
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=DE

network={{
    ssid="{ssid}"
    psk="{psk}"
    key_mgmt=WPA-PSK
}}
"""

def write_config_file(config: str, path: str = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"):
    with open(path, "w") as file:
        file.write(config)
    subprocess.run(["sudo", "chmod", "600", path])

def bring_up_interface(interface: str = "wlan0"):
    subprocess.run(["sudo", "ip", "link", "set", interface, "up"])

def start_wpa_supplicant(interface: str = "wlan0", config_path: str = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"):
    subprocess.run(["sudo", "killall", "wpa_supplicant"], stderr=subprocess.DEVNULL)
    subprocess.run([
        "sudo", "wpa_supplicant",
        "-B",  # Run in background
        "-i", interface,
        "-c", config_path
    ])

def run_dhclient(interface: str = "wlan0"):
    subprocess.run(["sudo", "dhclient", interface])

def get_connected_ssid(interface: str = "wlan0") -> str:
    result = subprocess.run(["iwgetid", interface, "-r"], capture_output=True, text=True)
    return result.stdout.strip()

def connect_wifi(ssid: str, psk: str):
    print(f"🔧 Connecting to SSID: {ssid}")
    config = create_wpa_config(ssid, psk)
    write_config_file(config)
    bring_up_interface()
    start_wpa_supplicant()
    
    print("⏳ Waiting for connection...")
    for _ in range(10):
        time.sleep(2)
        current_ssid = get_connected_ssid()
        if current_ssid == ssid:
            print(f"✅ Connected to {ssid}")
            run_dhclient()
            return True
        else:
            print(f"🔄 Still trying... (current: '{current_ssid}')")
    
    print("❌ Failed to connect to Wi-Fi")
    return False



def get_configured_ssid(path: str = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"):
    if not os.path.isfile(path):
        print(f"❌ File not found: {path}")
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'^ssid=(.+)$', content, re.MULTILINE)
            if match:
                ssid_value = match.group(1)
                print(f"📶 SSID: {ssid_value}")
                return ssid_value
            else:
                print("❌ SSID not found.")
    except Exception as e:
        print(f"⚠️ Error reading file: {e}")
