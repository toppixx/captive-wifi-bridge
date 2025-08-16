from flask import Flask, render_template, request, redirect, url_for
import subprocess

app = Flask(__name__)

def scan_wifi():
    result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL', 'dev', 'wifi'], capture_output=True, text=True)
    networks = []
    for line in result.stdout.strip().split('\n'):
        if line:
            ssid, signal = line.split(':')
            if ssid:  # skip hidden SSIDs
                networks.append({'ssid': ssid, 'signal': signal})
    return networks

def connect_wifi(ssid, password):
    result = subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        success, message = connect_wifi(ssid, password)
        exit()
        return render_template('result.html', success=success, message=message)

    networks = scan_wifi()
    return render_template('index.html', networks=networks)

@app.route('/result')
def result():
    return redirect(url_for('index'))

@app.route('/hotspot-detect.html')
def hotspot_detect():
    return "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>", 200

@app.route('/generate_204')
def android_check():
    return "", 200

@app.route('/ncsi.txt')
def windows_check():
    return "Microsoft NCSI", 200

if __name__ == '__main__':
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=6996)  
