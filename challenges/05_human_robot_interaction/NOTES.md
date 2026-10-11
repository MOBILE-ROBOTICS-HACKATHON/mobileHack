# NOTES: Challenge 05 · Intuitive Human-Robot Interaction (Robot Whisperer · Beyond the Joystick)

Priority for you: ★ (secondary). Plan: `ROADMAP.md`.

## 1. The challenge in plain words
Design an **interface that lets a person communicate with a robot naturally**: XR headsets, gestures, body/hand tracking, wearables, haptics, IoT sensors: any modality. **Judged on usability, responsiveness and intuitiveness**, not on algorithm complexity. A simple but polished and fast interface wins over a complicated laggy one.

Hardware: 2× HoloLens 2, Meta Quest, NUC PCs, Arduino/ESP32/D1 Mini kits, soldering stations, 3D printers; any robot (Spot, TurtleBots…).

## 2. Concepts
**HRI loop**: human signal → perception/interpretation → command → robot acts → **feedback to the human** (visual, audio, haptic) → human adjusts. Without feedback the interface feels dead.

**Design principles**: natural mappings (lean right = turn right), low latency (<150 ms), deadzones + smoothing (EMA) to remove jitter, **modes and safety** (stop gesture, dead-man switch, auto-stop on tracking loss), discoverability, error forgiveness.

**Modalities**
- *Hand/body tracking*: MediaPipe (hands 21 landmarks; pose 33). Pure vision, runs on CPU.
- *Voice*: push-to-talk → Whisper → intent parser (rules or small LLM) → command; confirm with TTS.
- *Web UI*: browser app ↔ ROS via **rosbridge** WebSocket (roslibjs); tap-to-navigate on a map; joystick widget; camera stream.
- *XR*: Unity + ROS-TCP-Connector, or WebXR; holograms for waypoints, robot path visualisation, gaze/hand pointing. Highest wow, highest setup risk: get a mentor.
- *Wearables/IoT*: ESP32 + IMU/flex/pressure sensors; send over Wi-Fi (UDP/WebSocket/MQTT) or micro-ROS; a bridge node publishes `cmd_vel`.
- *Haptics*: vibration motor/buzzer on ESP32 driven by lidar proximity → the human *feels* the robot's surroundings.

**Evaluation** (juries like numbers): task completion time, error count, latency (ms), SUS-style questionnaire with 3–5 test users.

## 3. Packages
| Package | Role |
|---|---|
| `rosbridge_suite` (installed) | JSON/WebSocket ↔ ROS bridge: web, Unity, anything |
| `mediapipe` (pip, on demand) | hand/pose/face landmarks |
| `opencv` (installed) | camera capture, drawing feedback overlays |
| `faster-whisper` (on demand) | offline speech-to-text |
| `pyttsx3` / `piper` (on demand) | text-to-speech feedback |
| `websockets`, `paho-mqtt` (on demand) | ESP32/IoT bridges |
| `teleop_twist_joy` (installed) | gamepad baseline to compare against |
| Unity + ROS-TCP-Connector | XR apps (not in Docker) |
Install on demand inside the container: `pip3 install mediapipe "numpy<2"`.

## 4. The code
`src/gesture_teleop.py`: webcam → MediaPipe hand → `cmd_vel` (hand height = speed, hand x = turn, fist = stop). Test the vision part anywhere: `python3 src/gesture_teleop.py --no-ros`. (Inside Docker, `cv2.imshow` needs `opencv-python` with GUI; if the window fails, use `--no-ros` on the host venv.)

## 5. What to DO (≈5 h)
1. Run rosbridge: `ros2 launch rosbridge_server rosbridge_websocket_launch.xml` and write a 20-line HTML page (roslibjs) that publishes `cmd_vel`.
2. `pip3 install mediapipe` and run `gesture_teleop.py --no-ros`; tune mapping, add deadzone and smoothing; measure latency.
3. Voice: push-to-talk Whisper → "go forward", "stop", "turn left".
4. (Optional) ESP32 sending tilt over UDP → a Python node → `cmd_vel`.
5. Run a 3-person usability test and note results.

## 6. Venue preparation
- Ask mentors early about HoloLens/Quest access and existing Unity projects.
- Decide the single most intuitive interaction and polish it; add on-screen feedback (what the system understood).
- Prepare a demo where a non-expert (a juror) can try it in 30 seconds.

## 7. Pitfalls
| Problem | Fix |
|---|---|
| Jittery control | EMA filter, deadzone, rate-limit |
| Accidental commands | explicit "arm" gesture, stop on lost tracking |
| Lighting breaks tracking | test on site; add a fallback (keyboard) |
| Latency | resize frames, run MediaPipe lite model, avoid network hops |
| XR setup rabbit-hole | timebox to 2 h; fall back to web UI |

## 8. Glossary
EMA · deadzone · haptic · landmark · micro-ROS · rosbridge · SUS · WebXR · roslibjs.

## 9. Checklist
- [ ] I can drive the sim robot through a web page via rosbridge.
- [ ] I ran hand tracking and understand the landmark indices.
- [ ] I know three safety features an interface needs.
- [ ] I have a plan to measure latency and usability.
