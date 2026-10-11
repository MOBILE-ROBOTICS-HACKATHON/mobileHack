# NOTES: Challenge 06 · Hack the Service Bot (Plato robots)

Priority for you: ★ (secondary). Plan: `ROADMAP.md`.

## 1. The challenge in plain words
Four **Plato** service robots are provided and the organisers stress "**no closed source**". Your job: figure out how they work, take control of them (reverse-engineer, hijack, repurpose) and make them move under *your* software. It rewards curiosity, systematic investigation, and linking things together (network ↔ robot ↔ ROS 2). The theme is **digital sovereignty**: owning and controlling your robot without vendor cloud lock-in.

You don't know in advance the robot's hardware or software. Prepare a *method* and the tools.

## 2. Concepts
**Attack surface / interfaces a service robot may expose**
- **Network**: Wi-Fi/Ethernet; services on TCP/UDP ports: web UI (80/8080), SSH (22), **ADB** (5555 if Android-based), MQTT (1883), WebSocket/REST APIs, **rosbridge** (9090), ROS 1 master (11311) or ROS 2 DDS (7400+ UDP).
- **Software**: often Android or embedded Linux (maybe ROS inside); a vendor app talks to it via HTTP/WebSocket/MQTT/Bluetooth.
- **Hardware**: USB/serial/CAN to motor controllers (last resort).

**Reverse-engineering toolbox**
- *Recon*: `nmap` (open ports/services), `curl`/browser (web UIs, endpoints), mDNS/Bonjour (`avahi-browse`).
- *Traffic capture*: Wireshark / `tcpdump` while the vendor app drives the robot; `mitmproxy` for HTTP(S) from a phone app.
- *App analysis*: pull the APK (`adb pull`), decompile (`jadx`, `apktool`), grep for URLs, endpoints, tokens.
- *Replay*: reproduce a captured command with `curl`/Python (`requests`, `websockets`, `paho-mqtt`).
- *Minimal control*: find the smallest message that moves the robot.

**Bridging to ROS 2**: write a node that subscribes `geometry_msgs/Twist` on `cmd_vel` and translates to the robot's protocol (HTTP POST, WebSocket message, serial bytes). Publish what you can read back (battery, pose, bumper) as topics. Add speed caps and a watchdog (stop when `cmd_vel` stops).

**Ethics and rules**: do this only on the devices provided/authorised. Document findings responsibly (e.g., "default credentials exposed"). The pitch angle is *liberation*, not exploitation.

## 3. Packages and tools
| Tool | Role | Where |
|---|---|---|
| `nmap` | port/service scan | container (installed) |
| `curl`, `jq`, `websocat`, `mosquitto-clients` | probe REST/WebSocket/MQTT | host (`sudo apt install ...`) |
| Wireshark / `tcpdump` | capture traffic | host |
| `adb` (`android-tools-adb`) | Android debug shell, APK extraction | host |
| `jadx`, `apktool` | decompile Android apps | host |
| `mitmproxy` | intercept HTTP(S) | host (`pip install mitmproxy` or apt) |
| Python `requests`, `websockets`, `paho-mqtt`, `scapy`, `pyserial` | write the control client | pip |
| `rclpy`, `geometry_msgs` | the ROS 2 wrapper | container |
| `rosbridge_suite` | if the robot already speaks rosbridge | container |

## 4. The code
`src/recon.sh <robot-ip>`: ping + nmap top ports + full port scan + service versions + HTTP probes; saves results to `recon_<ip>/`.

## 5. What to DO (≈4 h of prep)
1. Practise recon on a device you own (router, printer, Raspberry Pi): run `recon.sh`, interpret every open port.
2. Practise traffic analysis: capture your phone talking to a smart-home gadget with mitmproxy or Wireshark.
3. Write a 30-line ROS 2 node that turns `cmd_vel` into HTTP POSTs to a toy Flask server (see skeleton below).
4. Read the OWASP IoT Top 10 and one robotics-security write-up (e.g. on service-robot vulnerabilities).
5. Prepare a pitch angle: digital sovereignty, offline operation, open protocol.

```python
# cmd_vel -> HTTP skeleton (replace URL/payload after reverse-engineering)
import rclpy, requests
from rclpy.node import Node
from geometry_msgs.msg import Twist
class Bridge(Node):
    def __init__(self):
        super().__init__("plato_bridge")
        self.create_subscription(Twist, "cmd_vel", self.cb, 10)
    def cb(self, m):
        v = max(-0.3, min(0.3, m.linear.x)); w = max(-1.0, min(1.0, m.angular.z))   # safety clamps
        requests.post("http://ROBOT_IP:PORT/api/move", json={"v": v, "w": w}, timeout=0.2)
def main(): rclpy.init(); rclpy.spin(Bridge())
```

## 6. Venue preparation
- Bring a laptop with Wireshark, adb, mitmproxy ready and a **USB-Ethernet adapter**; may need a direct link to the robot.
- Start with docs/teardowns of "Plato" robots as soon as the model is known (FCC ID, vendor SDK, forums).
- Use the `--net=host` container so the robot's network is directly reachable.
- Timebox each avenue (30 min); if it fails, try the next interface.

## 7. Pitfalls
| Problem | Fix |
|---|---|
| Can't reach the robot | wrong subnet; set a static IP on the same /24; check cables; firewall |
| HTTPS traffic unreadable | mitmproxy cert on the phone; app may pin certs → use jadx/frida (advanced) or other interfaces |
| Robot jerks / runs away | clamp speeds, send zeros on timeout, keep it on blocks for first tests |
| Commands work once then fail | tokens/session; replay the login flow |

## 8. Glossary
ADB · APK · mDNS · MQTT · mitm · nmap · REST · rosbridge · WebSocket · digital sovereignty.

## 9. Checklist
- [ ] I can scan a host and explain each open port.
- [ ] I captured and read app traffic at least once.
- [ ] I have the `cmd_vel` → protocol bridge skeleton ready.
- [ ] Tools installed on the host (`wireshark`, `adb`, `mitmproxy`, `jq`).
