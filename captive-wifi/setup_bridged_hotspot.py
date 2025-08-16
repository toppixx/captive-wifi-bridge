import subprocess
def run(cmd, shell=False, printToConsole=True):
    if printToConsole:
      print(f"\n▶️  Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.run(cmd, shell=shell, check=True)

def start(UPSTREAM_SSID, UPSTREAM_PASSWORD):
    # Configuration variables
    TC_HOTSPOT = "tc_hotspot"
    TC_HOTSPOT_PASSWORD = "password123"


    print("📡 Setting up bridged Wi-Fi hotspot...")

    # Disable services
    run(["sudo", "systemctl", "mask", "hostapd"])
    run(["sudo", "systemctl", "disable", "hostapd"])
    run(["sudo", "systemctl", "mask", "dnsmasq"])
    run(["sudo", "systemctl", "disable", "dnsmasq"])

    # Clear iptables rules
    run(["sudo", "iptables", "-F"])
    run(["sudo", "iptables", "-t", "nat", "-F"])

    # Disable dhcpcd for wlan interfaces
    run("echo 'denyinterfaces wlan0 wlan1' | sudo tee -a /etc/dhcpcd.conf", shell=True)

    # Bridge setup
    run(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "wlan0", "-j", "MASQUERADE"])
    run(["sudo", "iptables", "-A", "FORWARD", "-i", "wlan0", "-o", "wlan1", "-j", "ACCEPT"])
    run(["sudo", "iptables", "-A", "FORWARD", "-i", "wlan1", "-o", "wlan0", "-m", "state",
        "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])

    # Delete old hotspot connection if exists
    try:
        result = subprocess.run(["nmcli", "--terse", "connection", "show"],
                                capture_output=True, text=True, check=True)
        if TC_HOTSPOT in result.stdout:
            run(["sudo", "nmcli", "connection", "delete", TC_HOTSPOT])
    except subprocess.CalledProcessError:
        print("⚠️ Failed to list connections")

    # Add new hotspot
    run(["nmcli", "con", "add", "type", "wifi", "ifname", "wlan0", "con-name", TC_HOTSPOT,
        "autoconnect", "yes", "ssid", TC_HOTSPOT])
    run(["nmcli", "con", "modify", TC_HOTSPOT, "ipv4.addresses", "192.69.42.1/24"])
    run(["nmcli", "con", "modify", TC_HOTSPOT, "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg", "ipv4.method", "shared"])
    run(["nmcli", "con", "modify", TC_HOTSPOT, "wifi-sec.key-mgmt", "wpa-psk"])
    run(["nmcli", "con", "modify", TC_HOTSPOT, "802-11-wireless-security.proto", "rsn"])
    run(["nmcli", "con", "modify", TC_HOTSPOT, "wifi-sec.psk", TC_HOTSPOT_PASSWORD], False, False)
    print("\n▶️  Running: " + " ".join(["nmcli", "con", "modify", TC_HOTSPOT, "wifi-sec.psk", "*******",]))

    run(["nmcli", "con", "up", TC_HOTSPOT])

    # Connect to upstream Wi-Fi
    print("\n🔌 Connecting wlan1 to upstream Wi-Fi...")
    run(["nmcli", "device", "wifi", "connect", UPSTREAM_SSID,
        "password", UPSTREAM_PASSWORD, "ifname", "wlan1"], False, False)
    print("\n▶️  Running: " + " ".join(["nmcli", "device", "wifi", "connect", UPSTREAM_SSID,
        "password", "*******", "ifname", "wlan1"]))
    print("\n✅ Setup complete! Reboot to activate bridged hotspot.")


if __name__ == "__main__":
    UPSTREAM_SSID = "Rabbit Hole"
    UPSTREAM_PASSWORD = "6kozzzAPQXa!YEfy"
    start(UPSTREAM_SSID, UPSTREAM_PASSWORD)
