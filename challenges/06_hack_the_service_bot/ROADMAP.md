# Challenge 06: Hack the Service Bot (Plato robots)

> Brief: four **Plato** service robots, *no closed source*. Reverse-engineer, hijack, repurpose, get them moving under your control.
> Ideal for digital sovereignty and open robotics platforms.

This is **reverse-engineering + ROS bridging**. The exact robot is unknown until the event, so prep is about *workflow*.
Only test devices you are authorised to test (the organisers provide these for exactly this).

## Method
1. **Observe**: what does it do at power-up? Vendor app? Touchscreen? Search the model online first (teardowns, FCC filings, GitHub, forums). Ten minutes here can save hours.
2. **Network recon**: join its Wi-Fi or plug in Ethernet, then run `src/recon.sh <ip>` (ping, nmap, HTTP probes). Typical open ports and what they mean:
   - 22: SSH
   - 80/8080: web UI or REST API
   - 5555: **adb** (Android-based robot)
   - 1883: MQTT
   - 9090: rosbridge
   - 11311: ROS 1 master
   - 7400+: DDS (ROS 2)
3. **Find the control interface** (try in this order):
   - Is it already ROS? `ros2 topic list` with the right `ROS_DOMAIN_ID`.
   - Web or REST API: browser dev tools, then `curl`.
   - Android: `adb connect <ip>:5555`, `adb shell`, `pm list packages | grep -i <vendor>`, `adb pull` the APK, inspect with `jadx` or `apktool` for endpoints and keys.
   - Proprietary protocol: capture traffic with Wireshark or `tcpdump` while the vendor app drives the robot, then replay.
   - Serial/CAN to the motor controller: last resort.
4. **Replay and minimise**: find the smallest message that makes it move. Send it from Python.
5. **Wrap in ROS 2**: write a node that subscribes `cmd_vel` and translates to the robot protocol. It should also publish `odom`/`battery` if available. Add velocity caps and a watchdog.
6. **Repurpose**: with `cmd_vel` working, the robot joins everything else (Nav2, teleop, vision follow, your imitation policy).

## Tools to install now
`nmap`, `wireshark`, `adb` (`android-tools-adb`), `jadx`, `apktool`, `mitmproxy`, `curl`, `jq`, `websocat`, `mosquitto-clients`, and Python `requests`, `websockets`, `paho-mqtt`, `scapy`.
(`nmap` is already in the Docker image. The rest are best installed on the **host**: `sudo apt install wireshark android-tools-adb mosquitto-clients jq curl`.)

## Practice before the event
- Run `nmap` and `curl` against a device you own (router, printer, Raspberry Pi) and map what it exposes.
- Run `mitmproxy` against a phone app to see HTTP/HTTPS calls.
- Write a 30-line ROS 2 node that turns `cmd_vel` into HTTP POSTs to a dummy Flask server. That is the final-step skeleton.
- Skim the OWASP IoT Top 10 and what "digital sovereignty" means in robotics (no cloud lock-in, local control, open protocols). It makes a good pitch angle.

## Pitch angles
- "Liberated": the robot was cloud-locked, now it runs fully local ROS 2.
- A short security note: what was exposed (open adb, default password), responsibly framed.
- Combine with another track: a gesture-controlled or vision-guided Plato.
