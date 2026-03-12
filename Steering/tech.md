# Smart Rover Technical Spec Sheet

## System Overview

The Smart Rover is a two-subsystem educational robotics platform combining Snap Circuits electronics with a Raspberry Pi compute module.

### Subsystem 1: Smart Module (Compute + Vision)
- **Computer:** Raspberry Pi 4
- **Camera:** Embedded PiCamera (within Smart Module housing), fixed forward-facing, cannot pan or tilt
  - Max resolution: 2592 x 1944 (framerate 15)
  - Min resolution: 64 x 64
  - Typical working resolution: 640 x 480 (framerate 30)
  - Rotation: configurable digitally (0, 90, 180 degrees) — does not change physical angle
  - Settings: ISO, shutter speed, exposure mode, AWB, contrast, brightness
- **OS:** Raspberry Pi OS
- **IDE:** Thonny Python IDE
- **Language:** Python (using RPi.GPIO, picamera, numpy, cv2 libraries)
- **Power:** USB-C power cord ONLY (never AA batteries, never other sources)

### Subsystem 2: Rover Body (Mobility + Power)
- **Power:** 1.5V AA batteries ONLY (in rover body battery compartment)
- **Motors:** Two DC motors (left and right), gear-driven wheels
- **Chassis:** Rover body with Snap Circuits mounting grid on rear

## Power Architecture

| Subsystem | Power Source | Warnings |
|---|---|---|
| Smart Module (Pi) | USB-C wall adapter (provided) | NEVER use AA batteries or other sources |
| Rover Body (motors/circuits) | 1.5V AA batteries | NEVER use external power, Snap Circuits battery holders, or outlets |

Power is intentionally split between subsystems. Short-circuit avoidance is a core design constraint.

## Motor Control

### Motor Control Module (U8)
- Contains 16 transistors and resistors
- Interfaces between Pi GPIO logic signals and motor drive current
- Acts as the power interface layer between low-power Pi pins and high-current motors

### GPIO Pin Mapping (BOARD mode)

| Pin # (BOARD) | Snap # | Function | Direction |
|---|---|---|---|
| 35 | 1 | Left Forward | Output |
| 31 | 2 | Left Backward | Output |
| 26 | 3 | Right Forward | Output |
| 21 | 4 | Right Backward | Output |
| 18 | 6 | Button / Phototransistor / Selector C | Input |
| 7 | 7 | Selector A | Input |

## Driving Mechanics and Limitations

### Drive System: Differential (Tank-Style) Steering
The rover uses differential drive with two independently controlled motors (left and right). There are no steering joints, axles, or articulated linkages. All turning is achieved by running the two motors in different directions.

### Movement Capabilities

| Movement | Left Motor | Right Motor | Description |
|---|---|---|---|
| **Forward** | Forward (pin 35 HIGH) | Forward (pin 26 HIGH) | Both motors drive forward simultaneously |
| **Backward** | Backward (pin 31 HIGH) | Backward (pin 21 HIGH) | Both motors drive in reverse simultaneously |
| **Left Turn (pivot)** | Backward (pin 31 HIGH) | Forward (pin 26 HIGH) | Left motor reverses while right drives forward; rover pivots left in place |
| **Right Turn (pivot)** | Forward (pin 35 HIGH) | Backward (pin 21 HIGH) | Right motor reverses while left drives forward; rover pivots right in place |

### Limitations and Constraints

1. **No variable speed control:** Motors are binary on/off (GPIO HIGH/LOW). No PWM speed control. The rover cannot make gradual curves; it can only pivot-turn or drive straight.
2. **No proportional steering:** Cannot arc or curve. Turning is always a full pivot (one motor forward, one backward).
3. **Time-based control only:** All movement duration is controlled by `sleep()` timing. No encoder feedback, odometry, or position sensing.
4. **No obstacle detection:** No proximity/distance sensors. The camera can detect light and color but cannot measure distance.
5. **Open-loop control:** No feedback loop for motor position or speed. The rover cannot confirm it actually traveled the intended path.
6. **Zero turning radius only:** Tank-style spin in place. No wide arcing turns are possible.
7. **Surface and battery dependent:** Performance varies with surface friction. AA battery voltage sag affects motor speed over time.
8. **Fixed forward-facing camera:** The camera faces forward at the rover's height from the Smart Module housing. It cannot pan, tilt, or look downward at the ground. Digital rotation settings only change image orientation, not the physical viewing angle.
9. **One direction per motor at a time:** Each motor direction is a single GPIO pin. Never activate both forward and backward on the same motor simultaneously.

### Default Timing Values (from solution files)

| Parameter | Default Value | Unit |
|---|---|---|
| Forward_Time | 2 | seconds |
| Backward_Time | 1 | seconds |
| Left_Turn_Time | 0.5 | seconds |
| Right_Turn_Time | 0.5 | seconds |
| Wait_Time | 0.5 - 1 | seconds |

## Components List

### Core Components (included in every kit)
- Rover Body (with motors and AA battery compartment)
- Smart Module (Raspberry Pi 4 + camera in housing)
- Base Grid (circuit mounting platform)
- Motor Control module (U8)
- Snap Wires: 1-snap (x2), 2-snap (x6), 3-snap (x2), 4-snap (x1), 5-snap (x1), 6-snap (x1), 7-snap (x1)
- White LED (D4)
- Horn (W1)
- Slide Switch (S1)
- Resistors: 100 Ohm (R1 x1), 1K Ohm (R2 x4)
- Capacitors: 0.02 microF (C1 x1), 100 microF (C4 x2)
- USB cable and wall power adapter

### Optional Components (per customization)
- Press Switch (S2)
- Selector (S8) — 3-input switch (A, B, C buttons)
- Phototransistor (Q4) — light-dependent current control
- Programmable Fan (M8) — motor with LED circuit
- Speaker (SP)
- NPN Transistor (Q2)
- Color Changing LED (D8)
- Slow Changing LED (D12)
- Jumper Wires (Orange, Yellow, Green, Blue, Gray, White)
- 3D Snap

## Sensor Capabilities

| Sensor | Type | Signal | Usage |
|---|---|---|---|
| Press Switch (S2) | Digital | HIGH/LOW | Button input, trigger actions |
| Selector (S8) | Digital (3-channel) | A/B/C pins | Multi-input selection |
| Phototransistor (Q4) | Analog-ish (digital threshold) | HIGH/LOW via GPIO | Light level detection |
| PiCamera | Image (RGB/HSV) | Array data via picamera library | Color detection, light detection, vision |

## Software Stack
- OS: Raspberry Pi OS
- IDE: Thonny Python IDE
- Language: Python
- Libraries: RPi.GPIO, time, picamera, picamera.array, cv2 (OpenCV), numpy
- Project files pre-loaded at /home/pi/Desktop/Projects

## Project Progression Summary

| # | Project | Key Concept | Components Used |
|---|---|---|---|
| 1 | Blinking LED | Variables, loops, GPIO output | Smart Module, LED |
| 2 | Light-Activated LED | Input/output | Smart Module, Press Switch, LED |
| 3 | Selector Output | Functions | Smart Module, Selector, LED, Horn |
| 4 | Programmed Driving | Motor control, driving functions | Smart Module, Motor Control |
| 5 | Timed Driving | Callback functions, timing | Smart Module, Press Switch, Motor Control |
| 6 | Light-Activated Driving | Loop complexity, if/else | Smart Module, Phototransistor, Motor Control |
| 7 | Controlled Driving | Complex logic, true/false | Smart Module, Selector, Motor Control |
| 8 | Introduction to Camera | Camera settings | Smart Module |
| 9 | Light Detection | HSV image processing | Smart Module, LED |
| 10 | Color Detection | RGB analysis, object detection | Smart Module, Press Switch, Horn, LED |
| 11 | Color-Detection Driving | Autonomous driving (intro) | Smart Module, Press Switch, Motor Control |
| 12 | Light-Seeking Driving | Autonomous driving (intermediate) | Smart Module, Press Switch, Motor Control |
| 13 | Open-Ended Project | Student-designed | Any combination |
