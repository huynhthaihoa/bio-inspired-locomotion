# Central pattern generator (CPG), from scratch

**Intuition:** a CPG is an internal metronome for movement. It ticks rhythmically by itself, and each tick tells the legs (or fins, or body segments) what to do: lift, swing, plant, push. Nothing outside has to say "now step" every time.

## 1. In animals
Walking, swimming and breathing are rhythmic, but your brain doesn't plan each step one by one.
Networks of neurons in the spinal cord produce the rhythm on their own. Classic experiments on cats and lampreys showed this rhythm continues even with the brain's input largely cut off.
The brain sets the speed and direction. The CPG produces the beat.

## 2. The three parts
Part |	What it does	| Everyday analogy |
| --- | --- | --- |
| Oscillator |	Produces a repeating cycle |	A metronome ticking |
|Coupling |	Keeps the legs' oscillators at fixed timing offsets from each other; that pattern of offsets is the gait |	Rowers keeping stroke together |
| Sensory feedback |	Nudges the rhythm when reality disagrees, e.g. a foot hits the ground early |	The metronome speeding up or slowing down to follow the dancer |

## 3. The key quantity: phase
- **Phase (φ)** says where you are in one cycle. It runs from 0 to 1, then wraps back to 0, like the hand of a clock.
- In the simplest model it grows at a constant rate: φ̇ = ω.
 - φ̇ is how fast the phase changes.
 - ω is the step frequency, in cycles per second.

**Worked example:** a hexapod in a tripod gait, with ω = 1 cycle/s.

- The six legs form two groups of three, A and B, half a cycle apart (offset 0.5).
- From φ = 0 to 0.5, group A is on the ground (stance) and group B swings forward.
- From φ = 0.5 to 1, they swap.
- So from φ alone, at any moment, you know which legs should be on the ground.

**Coupling** pulls each leg's phase toward its intended offset from the others. If one leg lags, it speeds up a bit until the offset is restored.

## 4. Feedback is what makes it an estimator
- Suppose the CPG says a foot should touch down at φ = 0.50, but the contact sensor fires at φ = 0.45 (the ground was higher). That gap is a phase error.
- With feedback, the CPG shifts its phase toward what the sensors report. Once it stays synchronized, its phase is effectively an estimate of where the robot really is in its gait.
- That is the idea in the CTU lab's paper (Szadkowski, Prágr & Faigl 2021, §2.6): "If the CPG is synchronized to the sensory signals, the CPG acts as an estimator of the sensory phase."
When the phase error added up over one cycle crosses a threshold, they flag a mistiming, e.g. a leg hitting an obstacle or stepping into a hole.
