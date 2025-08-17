#!/usr/bin/env python3
import subprocess, time, os, signal
from flask import Flask, render_template_string, request
import re
import sys
import time
from wifi_tools import connect_wifi 
# ==== FLASK CONFIG =====
FLASK_HOST     = "0.0.0.0"
FLASK_PORT     = 80


# ===== WIFI CONFIG =====
CAPTICE_WIFI_CONFIG_SRC='captcher-wifi.conf'
STATIC_WIFI_CONFIG_SRC='static-wifi.conf'
DHCPCD_CONFIG_SRC='dhcpcd.conf'
DHCPCD_CONFIG_TARGET='\\tmp\\dhcpcd.conf'

# ===== Templates =====
INDEX_HTML = """
<!doctype html>
<title>Wi-Fi Setup</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<h2>Select a Wi-Fi Network</h2>
<form action="/connect" method="post">
  <label>SSID:</label>
  <select name="ssid">
    {% for net in networks %}<option>{{net}}</option>{% endfor %}
  </select>
  <label>Password:</label>
  <input type="password" name="password" required>
  <button type="submit">Connect</button>
</form>
<form action="/rescan" method="post">
  <button type="submit">scan again</button>
</form>
"""

RESULT_HTML = """
<!doctype html>
<title>Connection {{status}}</title>
<h2>Connection {{status}}</h2>
<p>{{message}}</p>
"""

# ===== Helpers =====
def getTime():
    millis = int(time.time() * 1000)
    return millis

timeStart = getTime()
def log(str):
    timeStamp = getTime()
    elapsed = timeStamp - timeStart
    print(f"[{elapsed}ms] {str}")
    
def run(cmd):
    p = subprocess.run(cmd, shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       text=True)
    return p.returncode, p.stdout.strip()

# ==== WIFI HELPERS =====
def logExecutedShell(cmd, logOutput=True):
    result = subprocess.run(cmd, capture_output=True, text=True)

    if logOutput == True:
        if result.stdout:
            log(f'Command ({" ".join(cmd)}) succeeded. Output: {str(result.stdout)}')
        elif result.stderr:
            log(f'Command ({" ".join(cmd)}) succeeded with warnings: {str(result.stderr)}')
        else:
            log(f'Command ({" ".join(cmd)}) succeeded. No output. {str(result.returncode)}')
    return result

def executeShellAsync(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
def initNetworkServices():
    logExecutedShell(["sudo", "systemctl", "mask", "wpa_supplicant.service"])
    logExecutedShell(["sudo", "systemctl", "stop", "wpa_supplicant"])
    logExecutedShell(["sudo", "systemctl", "mask", "wpa_supplicant@wlan0.service"])
    logExecutedShell(["sudo", "systemctl", "stop", "wpa_supplicant@wlan0"])
    logExecutedShell(["sudo", "systemctl", "mask", "NetworkManager.service"])
    logExecutedShell(["sudo", "systemctl", "stop", "NetworkManager"])
    logExecutedShell(["sudo", "pkill", "hostapd"])
    logExecutedShell(["sudo", "pkill", "wpa_supplicant"])
    logExecutedShell(["sudo", "pkill", "NetworkManager"])
    logExecutedShell(["sudo", "rfkill", "unblock", "all"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "down"])
    logExecutedShell(["sudo", "iw", "dev", "wlan0", "set", "type", "managed"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "up"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "down"])
    logExecutedShell(["sudo", "iw", "dev", "wlan1", "set", "type", "managed"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "up"])

def deInitNetworkServices():
    logExecutedShell(["sudo", "systemctl", "unmask", "wpa_supplicant.service"])
    logExecutedShell(["sudo", "systemctl", "start", "wpa_supplicant"])
    logExecutedShell(["sudo", "systemctl", "mask", "wpa_supplicant@wlan0.service"])
    logExecutedShell(["sudo", "systemctl", "stop", "wpa_supplicant@wlan0"])
    logExecutedShell(["sudo", "systemctl", "unmask", "NetworkManager.service"])
    logExecutedShell(["sudo", "systemctl", "start", "NetworkManager"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "down"])
    logExecutedShell(["sudo", "iw", "dev", "wlan0", "set", "type", "managed"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "up"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "down"])
    logExecutedShell(["sudo", "iw", "dev", "wlan1", "set", "type", "managed"])
    logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "up"])

def get_hostapd_pid(configPath):
    pid = 0
    try:
        ps = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
        grep = subprocess.Popen(["grep", configPath], stdin=ps.stdout, stdout=subprocess.PIPE, text=True)
        ps.stdout.close()
        output = grep.communicate()[0]  # This is your string result

        # Combine output or handle separately
        match = re.search(r'\s[+]?+(\d+)', output)
        if match:
            log("hostapd wifi pid found: " + match.group(1))
            pid = int(match.group(1))
        else:
            log("No match found.")
        log(pid)
    except Exception as e:
        log(f"Caught an error: {e}")
    return pid


def start_static_hotspot():
    logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "up"])
    executeShellAsync(["sudo", "hostapd", STATIC_WIFI_CONFIG_SRC])
    log(" ".join(["sudo", "hostapd", STATIC_WIFI_CONFIG_SRC]))

def stop_static_hotspot():
    # Get pid of the static hotspot
    pid = get_hostapd_pid("hostapd/" + STATIC_WIFI_CONFIG_SRC)
    if pid > 0:
        try:
            log("stop_static_hotspot_ killing process " + str(pid))
            logExecutedShell(["pkill", str(pid)])
            log("stop_static_hotspot_ killed process successfully "+ str(pid))
        except ProcessLookupError:
            log("stop_static_hotspot_ killed process failed!!")
            pass

def start_captive_hotspot():
    logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "up"])
    log(" ".join(["sudo", "hostapd", CAPTICE_WIFI_CONFIG_SRC]))
    executeShellAsync(["sudo", "hostapd", CAPTICE_WIFI_CONFIG_SRC])

def stop_captive_hotspot():
    pid = get_hostapd_pid("hostapd/" + CAPTICE_WIFI_CONFIG_SRC)
    if pid > 0:
        try:
            log("stop_captive_hotspot: killing process " + str(pid))
            logExecutedShell(["pkill", str(pid)])
            log("stop_captive_hotspot: killed process successfully "+ str(pid))
        except ProcessLookupError:
            log("stop_captive_hotspot: killed process failed!!")
            pass

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
    # add this to the config if ssid is hidden
    #    scan_ssid=1
    return config
    

def getExpectedSSSID(filePath = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"):
    try: 
        with open(filePath, "r") as file:
            content = file.read()
            ssid_line = re.search(r'ssid\s*=\s*".*?"', content)
            if ssid_line:
                print(ssid_line.group())  # Output: ssid="Rabbit Hole"
                match = re.search(r'ssid\s*=\s*"([^"]+)"', ssid_line.group())
                if match:
                    ssid_value = match.group(1)
                    print(f"Extracted SSID: {ssid_value}")
                    return ssid_value
                else:
                    print("SSID not found.")
                    return ""
    except Exception as e:
        print(f"⚠️ Error reading file: {e}")

# def connect_captive_hotspot(ssid: str, psk: str):
    # stop_captive_hotspot()
    # logExecutedShell(["sudo", "systemctl", "unmask", "wpa_supplicant@wlan0"])
    # logExecutedShell(["sudo", "systemctl", "stop", "wpa_supplicant@wlan0"])
    # config = create_wpa_config(ssid, psk)
    # filePath = "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    # with open(filePath, "w") as file:
    #     log(f"wpa_config file {filePath} written")
    #     print(f"config {config}")
    #     logExecutedShell(["sudo", "ip", "link", "set", "wlan0", "up"])
    #     logExecutedShell(["sudo", "systemctl", "enable", "wpa_supplicant@wlan0"])
    #     file.write(config)
    #     logExecutedShell(["sudo", "chmod", "600", "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"])
    #     # logExecutedShell(["sudo", "systemctl", "start", "wpa_supplicant@wlan0"])
    #     logExecutedShell(["sudo", "systemctl", "unmask", "wpa_supplicant"])
    #     logExecutedShell(["sudo", "wpa_supplicant", "-B", "-i", "wlan0", "-c", "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"])
    #     logExecutedShell(["sudo", "systemctl", "start", "wpa_supplicant"])
    #     print("🔄 Restarting wpa_supplicant@wlan0")
    #     # Wait until the control socket appears
    #     restarted = False
    #     for _ in range(3):  # up to 10 seconds
    #         time.sleep(3.3)
    #         if connect_wifi(ssid, "wlan0") == ssid:
    #             print("✅ Control socket found")
    #             restarted = True
    #         else :
    #             print(f"ssid ({ssid}) not connected")
    #     if restarted == False:
    #         print("❌ Control socket not found")

    #     if restarted == True:
    #         result = subprocess.run(
    #             ["sudo", "wpa_cli", "-i", "wlan0", "status"],
    #             capture_output=True,
    #             text=True
    #         )
    #         print("📶 wpa_cli output:\n", result.stdout)
    #     else:
    #         print("⚠️ Cannot run wpa_cli: control socket missing")
    #         result = logExecutedShell(["sudo", "dhclient", "wlan0"])
    #         log(result)
    #     # if result.returncode == 0:
    #     if True :
    #         log("checking for connected wifis")
    #         connectedSsid = get_connected_ssid(ssid, "wlan0")
    #         log(f"WPA wifi connected to ({connectedSsid})")
    #         log(f"WPA wifi ({ssid}) connection configured")
    #     else:
    #         log(f"WPA wifi ({ssid}) connection failed:\nstdOut: {str(result.stdout)}\nstdErr: {str(result.stderr)}\nresultCode: {result.returncode}")
    #     # return result.returncode
    #     return 0
    # return -1

def scan_networks(interface="wlan1"):
    try:
        stop_static_hotspot()
        # Run the command to scan Wi-Fi networks
        logExecutedShell(["sudo", "ip", "link", "set", "wlan1", "up"])
        logExecutedShell(["sudo", "iw", "dev", "wlan1", "set", "type", "managed"])
        output = subprocess.check_output(["sudo", "iw", "dev", interface, "scan"], text=True)
        # output2 = subprocess.check_output(["sudo", "ip", "link", "set", "wlan1", "down"])

        static_ssid = get_configured_ssid(STATIC_WIFI_CONFIG_SRC)
        print(f"static_ssid  {static_ssid}")
        captive_ssid = get_configured_ssid(CAPTICE_WIFI_CONFIG_SRC)
        print(f"captive_ssid  {captive_ssid}")
        networksToHide = [static_ssid, captive_ssid]

        # Parse the output for SSIDs and signal strength
        # log(output)
        networks = []
        for block in output.split("BSS ")[1:]:
            # log(block)
            ssid_match = re.search(r'SSID: (.+)', block)
            signal_match = re.search(r'signal: ([-\d.]+) dBm', block)
            if ssid_match and signal_match:
                ssid = ssid_match.group(1)
                signal = float(signal_match.group(1))
                if not ssid in networksToHide:
                    networks.append((ssid, signal))

        # Sort by signal strength (descending)
        filtered_networks = {}
        for ssid, signal in networks:
            if ssid not in filtered_networks or signal > filtered_networks[ssid]:
                filtered_networks[ssid] = signal

        # Convert back to list of tuples
        result = [(ssid, signal) for ssid, signal in filtered_networks.items()]

        result.sort(key=lambda x: x[1], reverse=True)
        log(result)
        return result

    except subprocess.CalledProcessError as e:
        log(f"Error scanning Wi-Fi: {e}")
        return []


# def get_connected_ssid(wlan_interface = "wlan0", ssid='any'):
#     try:
#         result = logExecutedShell(["sudo", "wpa_cli", "-i", wlan_interface, "status"])
#         connectedSSid = 'any'
#         print(result)
#         if result.returncode == 0:
#             if ssid != 'any':
#                 connectedSSid = ssid in result.stdout
#         return connectedSSid if ssid else "Not connected"
#     except subprocess.CalledProcessError:
#         return "Error retrieving SSID"
def get_connected_ssid(ssid, wlan_interface = "wlan0"):
    try:
        result = logExecutedShell(["iw", "dev"], False)
        # print(result)
        match = re.search(r'Interface wlan0\b[\s\S]*?\n\s*ssid\s+.*$', result.stdout, re.MULTILINE)
        # print(match)
        line = 'ssid="Rabbit Hole"'
        if match:
            line = match.group(0).strip()
            match = re.search(r'ssid="([^"]+)"', line)
            if match:
                ssid_value = match.group(1).strip()
                print(f"Extracted SSID: {ssid_value}")
                return ssid_value if ssid == ssid_value else "Not connected"
            else:
                print("No SSID found in the line.")
    except subprocess.CalledProcessError:
        print("Error retrieving SSID")
        return "Error retrieving SSID"
 

# ===== Flask App =====
app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(INDEX_HTML, networks=scan_networks())

@app.route("/rescan", methods=["POST"])
def rescan():
    return render_template_string(INDEX_HTML, networks=scan_networks())

@app.route("/connect", methods=["POST"])
def connect():
    ssidPost = request.form["ssid"]
    ssid = re.search(r"'(.*?)'", ssidPost).group(0).strip("'")
    psk  = request.form["password"]
    log(ssid)
    log("******")
    wif_connected = connect_wifi(ssid, psk)
    if wif_connected == True:
        stop_captive_hotspot()
        start_static_hotspot()
        return render_template_string(
            RESULT_HTML,
            status="Successful",
            message=f"Now connected to {ssid}!"
        )
    else:
        return render_template_string(
            RESULT_HTML,
            status="Failed",
            message=str(code)
        ), 400


if __name__ == "__main__":
    try:
        log("Running main process. Press Ctrl+C to interrupt.")
        ssid = getExpectedSSSID()
        print(ssid)
        log("Connected to: " + str(get_connected_ssid(ssid, "wlan0")))
        initNetworkServices()
        stop_static_hotspot()
        stop_captive_hotspot()
        start_captive_hotspot()
        # start_static_hotspot()
    
        app.run(host=FLASK_HOST, port=FLASK_PORT)

    except Exception as e:
        log(f"Caught an error: {e}")

    except KeyboardInterrupt:
        log("\n🛑 Ctrl+C detected! Executing cleanup task...")
        # Perform cleanup or intermediate action
        deInitNetworkServices()

    finally:
        log("✅ Shutdown")
        # Your next command or action here
        sys.exit(0) 
