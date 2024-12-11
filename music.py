import subprocess
import time

device_name = "LAMAX Beat SE-1"  # The friendly name of your Bluetooth device
mp3_path = "/home/admin/W/pi/demo.mp3"  # Path to the MP3 file you want to play

def run_cmd(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print("Command failed:", cmd)
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        raise RuntimeError("Command failed")
    return result.stdout.strip()

def get_device_mac_by_name(name):
    # Turn on scanning and look for device
    run_cmd("bluetoothctl -- timeout 5 scan on", check=False)
    time.sleep(5)
    # List devices
    output = run_cmd("bluetoothctl devices", check=False)
    # Expected line format: "Device XX:XX:XX:XX:XX:XX DeviceName"
    for line in output.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3:
            mac = parts[1]
            dev_name = parts[2]
            if dev_name.strip() == name:
                return mac
    return None

def ensure_bluetooth_powered():
    run_cmd("bluetoothctl power on")

def pair_and_connect(mac):
    # Trust device
    run_cmd(f"bluetoothctl trust {mac}")
    # Pair device
    run_cmd(f"bluetoothctl pair {mac}")
    # Connect device
    run_cmd(f"bluetoothctl connect {mac}")

def play_mp3(file_path):
    # Using GStreamer pipeline to play MP3
    # If the Bluetooth speaker is the default ALSA sink after connection,
    # this should play directly.
    cmd = f"gst-launch-1.0 filesrc location=\"{file_path}\" ! decodebin ! audioconvert ! audioresample ! alsasink"
    subprocess.run(cmd, shell=True)

def main():
    ensure_bluetooth_powered()

    print("Searching for Bluetooth device:", device_name)
    mac = get_device_mac_by_name(device_name)
    if mac is None:
        print(f"Device '{device_name}' not found. Make sure it is discoverable.")
        return

    print(f"Found device {device_name} at {mac}. Pairing and connecting...")
    pair_and_connect(mac)
    time.sleep(2)  # Give some time to ensure the device is fully connected.

    print("Playing MP3 file...")
    play_mp3(mp3_path)

if __name__ == "__main__":
    main()
