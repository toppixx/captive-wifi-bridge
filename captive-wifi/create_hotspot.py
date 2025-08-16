from PyAccessPoint  import AccessPoint

# Create and configure the access point
ap = AccessPoint(interface='wlan1',
                 ssid='MyHotspot',
                 password='securepassword123',
                 ip='192.168.45.1',
                 netmask='255.255.255.0',
                 gateway='192.168.45.1')

# Start the access point
ap.start()
print("Hotspot started on wlan1 with SSID: 'MyHotspot'")

# To stop the access point, you can call:
# ap.stop()
# print("Hotspot stopped.")