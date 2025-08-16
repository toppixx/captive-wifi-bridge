import subprocess
def run(cmd, shell=False, printToConsole=True):
    if printToConsole:
      print(f"\n▶️  Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.run(cmd, shell=shell, check=True)

def remove(WIFI_HOTSPOT, WIFI_CLIENT):
    # Bridge setup
    run(["sudo", "iptables", "-t", "nat", "-D", "POSTROUTING", "-o", "wlan0", "-j", "MASQUERADE"])
    run(["sudo", "iptables", "-D", "FORWARD", "-i", "wlan0", "-o", "wlan1", "-j", "ACCEPT"])
    run(["sudo", "iptables", "-D", "FORWARD", "-i", "wlan1", "-o", "wlan0", "-m", "state",
        "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])

    # Delete old hotspot connection if exists
    try:
        result = subprocess.run(["nmcli", "--terse", "connection", "show"],
                                capture_output=True, text=True, check=True)
        if WIFI_HOTSPOT in result.stdout:
            run(["sudo", "nmcli", "connection", "delete", WIFI_HOTSPOT])
    except subprocess.CalledProcessError:
        print("⚠️ Failed to list connections")

    # Delete old hotspot connection if exists
    try:
        result = subprocess.run(["nmcli", "--terse", "connection", "show"],
                                capture_output=True, text=True, check=True)
        if WIFI_CLIENT in result.stdout:
            run(["sudo", "nmcli", "connection", "delete", WIFI_CLIENT])
    except subprocess.CalledProcessError:
        print("⚠️ Failed to list connections")

if __name__ == "__main__":
    UPSTREAM_SSID = "Rabbit Hole"
    TC_HOTSPOT = "tc_hotspot"
    remove(UPSTREAM_SSID, TC_HOTSPOT)
