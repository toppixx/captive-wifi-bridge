DNSMASQ_CONFIG_SRC='dnsmasq.conf'
DNSMASQ_CONFIG_TARGET='\\tmp\\dnsmasq.conf'
DNSMASQ_PID='\\tmp\\dnsmasq.pid'


# ==== DNS MASQ HELPERS =====
def write_dnsmasq_conf():
    with open (DNSMASQ_CONFIG_SRC, "r") as file:
        cfg =  file.read()
        with open(DNSMASQ_CONFIG_TARGET, "w") as f:
            f.write(cfg)

def start_dnsmasq():
    write_dnsmasq_conf()
    # Remove old pid if present
    if os.path.exists(DNSMASQ_PID):
        os.remove(DNSMASQ_PID)
    subprocess.Popen([
        "dnsmasq",
        "--conf-file="+DNSMASQ_CONFIG_TARGET,
        "--pid-file="+DNSMASQ_PID
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_dnsmasq():
    if os.path.exists(DNSMASQ_PID):
        with open(DNSMASQ_PID) as f:
            pid = int(f.read().strip())
        try:
            log("stop_dnsmasq: killing process " + str(pid))
            logExecutedShell(["pkill", str(pid)])
            log("stop_dnsmasq: killed process successfully "+ str(pid))
        except ProcessLookupError:
            log("stop_dnsmasq: killed process failed!!")
            pass
        os.remove(DNSMASQ_PID)
    if os.path.exists(DNSMASQ_CONFIG_TARGET):
        os.remove(DNSMASQ_CONFIG_TARGET)
