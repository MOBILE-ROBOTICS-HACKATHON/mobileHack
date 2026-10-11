# Challenge 05: Intuitive Human-Robot Interaction (Robot Whisperer · Beyond the Joystick)

> Brief: interface for seamless human-robot communication: XR, gestures, body/hand tracking, wearables, haptics, IoT sensors.
> Judged on **usability, responsiveness, intuitiveness.**

**Hardware:** HoloLens 2 ×2, Meta Quest, NUC PCs, ESP32/Arduino kits, any ROS 2 robot (Spot, TurtleBots…), 5G network.

## Mental model
`human signal (gesture/voice/gaze/wearable)  →  interpretation  →  robot command  +  feedback to human (visual/audio/haptic)`
A good HRI project closes the loop with **feedback** (the human must *see/feel* what the robot understood) and has **safety** (dead-man, stop gesture).

## Options (pick by effort/wow)
| Modality | Stack | Effort | Notes |
|---|---|---|---|
| Hand gestures, webcam | MediaPipe → `cmd_vel` (`src/gesture_teleop.py`) | 1 h | easiest, robust demo |
| Full-body pose (follow-me, arms as joystick) | MediaPipe Pose / YOLO-pose | 2 h | combine with Challenge 03 |
| Voice commands | Whisper (tiny/base) STT → intent → Nav2 goal ("go to the door") | 3 h | noisy venue: use push-to-talk |
| Web UI joystick/map | `rosbridge_suite` + roslibjs/React (installed: `ros-humble-rosbridge-suite`) | 2–3 h | tap on map → `NavigateToPose` |
| XR (Quest/HoloLens) | Unity + ROS-TCP-Connector (ros2 branch) or WebXR over rosbridge | 6 h+ | big wow, big setup risk: use a mentor |
| Wearable / IoT | ESP32 + IMU/flex sensor → micro-ROS / MQTT / WebSocket → ROS 2 bridge | 3 h | tilt-to-steer glove |
| Haptic / audio feedback | vibration motor on ESP32 triggered by lidar proximity | 2 h | pairs great with any above |

## Study order (~5 h)
1. rosbridge: run `ros2 launch rosbridge_server rosbridge_websocket_launch.xml`, connect a 20-line HTML page with roslibjs, publish `cmd_vel`.
2. `src/gesture_teleop.py` (`--no-ros` first): tune mapping, add dead-zone, smoothing (EMA), safety fist-stop; measure latency camera→cmd_vel.
3. Voice: `pip install faster-whisper`; push-to-talk; rule-based or small LLM intent parser; confirm via TTS.
4. ESP32 → ROS: simplest = ESP32 sends UDP/WebSocket JSON; a Python ROS node converts to `Twist`. (micro-ROS is better but slow to set up.)
5. UX evaluation: a 5-question usability test with 3 colleagues (task completion time, errors, SUS-lite). Judges love evidence.

## Design principles for the jury
- **Intuitive:** no manual needed; natural mapping (lean right → turn right).
- **Responsive:** <150 ms end-to-end; show latency on screen.
- **Forgiving:** deadzones, smoothing, undo/stop, visible state ("robot sees you", "gesture: STOP").
- **Safe:** loss of tracking → robot stops.

## Packages
`mediapipe`, `faster-whisper`, `pyttsx3`/`piper` (TTS), `ros-humble-rosbridge-suite` (installed), `websockets`, `paho-mqtt`. Install on demand inside Docker (`pip3 install mediapipe "numpy<2"`).
