# #!/usr/bin/env python3
# import subprocess, sys, time
# from flask import Flask, render_template_string, request, redirect

# # ======= CONFIGURATION ========
# WIFI_IFACE   = "wlan0"
# HOTSPOT_SSID  = "SetupAP"
# HOTSPOT_PSK   = "setup1234"
# HOTSPOT_NAME  = "Hotspot"   # default NM connection name
# FLASK_HOST   = "0.0.0.0"
# FLASK_PORT   = 80

# # ======= HELPERS ============
# def run(cmd):
#     """Run shell cmd, return (exit_code, stdout)."""
#     p = subprocess.run(cmd, shell=True,
#                        stdout=subprocess.PIPE,
#                        stderr=subprocess.STDOUT,
#                        text=True)
#     return p.returncode, p.stdout.strip()

# def ensure_wifi_on():
#     """Power on the Wi-Fi radio if it’s off."""
#     run("nmcli radio wifi on")
#     time.sleep(1)  

# def create_hotspot():
#     """Bring up a temporary hotspot via nmcli."""
#     run(f"nmcli device wifi hotspot ifname {WIFI_IFACE}"
#         f" ssid {HOTSPOT_SSID} password {HOTSPOT_PSK}")

# def teardown_hotspot():
#     """Disable the hotspot connection."""
#     run(f"nmcli connection down {HOTSPOT_NAME}")

# def recreate_hotspot():
#     teardown_hotspot()
#     time.sleep(1)
#     create_hotspot()

# def scan_networks():
#     """Return a list of available SSIDs."""
#     code, out = run(f"nmcli -t -f SSID dev wifi list ifname {WIFI_IFACE}")
#     ssids = [s for s in out.splitlines() if s and not s.startswith("--")]
#     # Remove duplicates while preserving order
#     seen = set(); uniq = []
#     for s in ssids:
#         if s not in seen:
#             seen.add(s); uniq.append(s)
#     return uniq

# # ======= FLASK APP ==========
# app = Flask(__name__)

# INDEX_HTML = """
# <!doctype html>
# <title>Wi-Fi Setup</title>
# <h2>Select a Wi-Fi Network</h2>
# <form action="/connect" method="post">
#   <label for="ssid">SSID:</label>
#   <select name="ssid" id="ssid">
#     {% for net in networks %}
#     <option value="{{net}}">{{net}}</option>
#     {% endfor %}
#   </select><br><br>
#   <label for="password">Password:</label>
#   <input type="password" name="password" id="password" required><br><br>
#   <button type="submit">Connect</button>
# </form>
# """

# RESULT_HTML = """
# <!doctype html>
# <title>Connection {{status}}</title>
# <h2>Connection {{status}}</h2>
# <p>{{message}}</p>
# """

# @app.route("/")
# def index():
#     nets = scan_networks()
#     return render_template_string(INDEX_HTML, networks=nets)

# @app.route("/connect", methods=["POST"])
# def connect():
#     ssid = request.form.get("ssid")
#     psk  = request.form.get("password")
#     # Attempt to join the chosen network
#     code, out = run(f"nmcli device wifi connect '{ssid}' password '{psk}' ifname {WIFI_IFACE}")
#     if code == 0:
#         teardown_hotspot()
#         return render_template_string(RESULT_HTML,
#                                       status="Successful",
#                                       message=f"Connected to {ssid}!")
#     else:
#         return render_template_string(RESULT_HTML,
#                                       status="Failed",
#                                       message=out), 400

# if __name__ == "__main__":
#     ensure_wifi_on()
#     # 1) Spawn the hotspot
#     create_hotspot()
#     # 2) Wait for NM to settle
#     time.sleep(3)
#     # 3) Start Flask
#     app.run(host=FLASK_HOST, port=FLASK_PORT)


#!/usr/bin/env python3
import subprocess, time, os, signal
from flask import Flask, render_template_string, request

# ===== CONFIG =====
WIFI_IFACE     = "wlan0"
HOTSPOT_CONN   = "MyHotspot"
HOTSPOT_PASSWORD = "password123"
DNSMASQ_CONF   = "/tmp/dnsmasq-hotspot.conf"
DNSMASQ_PID    = "/tmp/dnsmasq-hotspot.pid"
FLASK_HOST     = "0.0.0.0"
FLASK_PORT     = 80

# ===== Templates =====
INDEX_HTML = """
<!doctype html>
<title>Wi-Fi Setup</title>
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
"""

RESULT_HTML = """
<!doctype html>
<title>Connection {{status}}</title>
<h2>Connection {{status}}</h2>
<p>{{message}}</p>
"""

# ===== Helpers =====
def run(cmd):
    p = subprocess.run(cmd, shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       text=True)
    return p.returncode, p.stdout.strip()

def write_dnsmasq_conf():
    cfg = f"""
interface={WIFI_IFACE}
dhcp-range=10.42.0.10,10.42.0.100,12h
dhcp-option=3,10.42.0.1
server=8.8.8.8
"""
    with open(DNSMASQ_CONF, "w") as f:
        f.write(cfg)

def start_dnsmasq():
    write_dnsmasq_conf()
    # Remove old pid if present
    if os.path.exists(DNSMASQ_PID):
        os.remove(DNSMASQ_PID)
    subprocess.Popen([
        "dnsmasq",
        "--conf-file="+DNSMASQ_CONF,
        "--pid-file="+DNSMASQ_PID
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_dnsmasq():
    if os.path.exists(DNSMASQ_PID):
        with open(DNSMASQ_PID) as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        os.remove(DNSMASQ_PID)
    if os.path.exists(DNSMASQ_CONF):
        os.remove(DNSMASQ_CONF)

def scan_networks():
    code, out = run(f"nmcli -t -f SSID dev wifi list ifname {WIFI_IFACE}")
    nets = [s for s in out.splitlines() if s and not s.startswith("--")]
    seen = set(); uniq = []
    for s in nets:
        if s not in seen:
            seen.add(s); uniq.append(s)
    return uniq

# ===== Flask App =====
app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string(INDEX_HTML, networks=scan_networks())

@app.route("/connect", methods=["POST"])
def connect():
    ssid = request.form["ssid"]
    psk  = request.form["password"]
    code, out = run(
        f"nmcli device wifi connect '{ssid}' password '{psk}' ifname {WIFI_IFACE}"
    )
    if code == 0:
        teardown_hotspot()
        return render_template_string(
            RESULT_HTML,
            status="Successful",
            message=f"Now connected to {ssid}!"
        )
    else:
        return render_template_string(
            RESULT_HTML,
            status="Failed",
            message=out
        ), 400

# ===== Hotspot Lifecycle =====
def clear_old_config():
    import subprocess
    # Run nmcli and capture the list of connection names
    try:
        result = subprocess.run(
            ["nmcli", "--terse", "connection", "show"],
            capture_output=True,
            text=True,
            check=True
        )
        connections = [line.split(":")[0] for line in result.stdout.splitlines()]
        
        if HOTSPOT_CONN in connections:
            print(f"[🧹] Found '{HOTSPOT_CONN}' — deleting...")
            subprocess.run(["sudo", "nmcli", "connection", "delete", HOTSPOT_CONN], check=True)

    except subprocess.CalledProcessError as e:
        print(f"[⚠️] Error running nmcli: {e}")

def create_hotspot():
    run("nmcli radio wifi on")
    run(f"nmcli con add type wifi ifname {WIFI_IFACE} con-name {HOTSPOT_CONN} autoconnect yes ssid {HOTSPOT_CONN}")
    

    print(f"nmcli connection modify {HOTSPOT_CONN} \
  802-11-wireless.mode ap \
  802-11-wireless.ssid {HOTSPOT_CONN} \
  802-11-wireless.band bg \
  802-11-wireless.channel 1 \
  ipv4.method shared \
  ipv6.method ignore \
  802-11-wireless-security.proto rsn \
  802-11-wireless-security.key-mgmt wpa-psk \
  802-11-wireless-security.psk \"{HOTSPOT_PASSWORD}\"")
    run(f"nmcli connection modify {HOTSPOT_CONN} \
  802-11-wireless.mode ap \
  802-11-wireless.ssid {HOTSPOT_CONN} \
  802-11-wireless.band bg \
  802-11-wireless.channel 1 \
  ipv6.method ignore \
  802-11-wireless-security.proto rsn \
  802-11-wireless-security.key-mgmt wpa-psk \
  802-11-wireless-security.psk {HOTSPOT_PASSWORD}")
    run(f"nmcli connection up {HOTSPOT_CONN}")
    time.sleep(2)  # allow interface & IP to settle
    start_dnsmasq()

def teardown_hotspot():
    stop_dnsmasq()
    run(f"nmcli connection down {HOTSPOT_CONN}")

if __name__ == "__main__":
    clear_old_config()
    create_hotspot()
    app.run(host=FLASK_HOST, port=FLASK_PORT)
