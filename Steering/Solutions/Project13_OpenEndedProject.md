# Project 13 - Open-Ended Project

There is no solution file for Project 13. This is an open-ended project where students design and build their own rover program using Kiro as their AI development assistant.

## Guidance

- Students should combine at least three concepts from Projects 1 through 12 (e.g., GPIO output, camera input, driving functions, sensor reading, color detection)
- Since this is open-ended, help students brainstorm ideas, break their idea into smaller steps, and work through each step incrementally
- Unlike previous projects, students are expected to write code from scratch rather than modifying a provided template
- Encourage students to test each piece of their code before combining them
- Refer students back to their previous projects for code examples and patterns when relevant

## Hardware Limitations to Keep in Mind

When a student proposes an idea, check it against these rover constraints. If the idea requires something the rover cannot do, explain the limitation clearly and help them reshape the idea into something achievable.

- **No variable speed or gradual curves:** Motors are on/off only (GPIO HIGH/LOW). The rover can drive straight or pivot-turn in place. It cannot arc, curve, or adjust speed. Ideas requiring smooth turning or speed ramping need to be redesigned around pivot-and-drive sequences.
- **No distance or obstacle sensing:** There are no proximity, ultrasonic, or IR distance sensors. The camera can see color and brightness but cannot measure how far away something is. Ideas like "stop before hitting a wall" are not feasible unless reframed as color/light-based detection.
- **Time-based movement only:** All driving is controlled by `sleep()` duration. There are no wheel encoders or odometry. The rover cannot know exactly how far it traveled or confirm it reached a destination.
- **Fixed forward-facing camera:** The camera cannot pan or tilt. It only sees what is directly ahead of the rover. To look in a different direction, the entire rover must pivot.
- **Battery-dependent performance:** Motor speed varies as AA batteries drain. A driving path that works with fresh batteries may behave differently later.

## Example Project Ideas to Suggest

- Color-sign navigation course: set up colored signs and program the rover to follow a sequence of commands (red = stop, green = go, blue = turn)
- Light-chasing with LED feedback: seek the brightest area using the camera and blink the LED when light is found
- Programmed dance routine: sequence of forward, backward, and pivot turns set to timed patterns with LED/horn effects
- Color-sorting patrol: drive a set route, stop and identify colors with the camera, and signal with LED or horn based on what it sees
- Simon Says driving: use the selector or button to queue up a sequence of moves, then replay them
- Morse code communicator: use the LED or horn to blink/beep messages in Morse code patterns
