# KTaNE
The project files for the real life keep talking and nobody explodes replica i'm working on. 
This uses raspberry pis as the main controller, since it's the only one I know, I have and because I'm not splurging 80 euro for an arduino 😉

UPDATE: holy shit they came out with a raspberry pi arduino clone for 8 euro let's fucking go


## Please do this and don't ignore

---------

- [ ] Add LCD to `Button` module (so it can display different messages) ---- _potentially just use a seperate LCD?_
- [ ] Buy an actual RGB LED so the `Button` module doesn't have to use three seperate LEDs
- [ ] Work on concept for `Wires` module
- [ ] Work on concept for `Simon` says module
- [ ] Work on concept for `Keypad` module ---- _current thoughts: 1x1 LCD-kinda thing on top of push-button like structure?_
- [ ] Work on concept for `Progress Bar` module ---- _custom module: has a progress LED bar, rotary encoder and button. it has multiple rules, changing when the button has to be pressed and how high the led progress bar has to be. probably could add an rgb led too, just to mix it up a bit? (like if you turn the progress bar up to a certain point the led switches to the next colour, going all the way through ROYGBP)_
- [ ] Work on concept for `Switches` module ---- _custom module: four custom military switches, switch them in a specific order (identical to wires)_


## Modules

---------

### [**Timer**](timer.py) \[ID:0\]

_[Confused?](https://ktane.fandom.com/wiki/Timer)_

This is the **core module**, it must be **always present** in a bomb. It does the main logic for the game (i.e. bomb explosion, countdown, etc)

> _"This module is going to be updated so often and rewritten so much that it might as well have a different name every time"_
> 
> Constantly being updated; be on the lookout for sneaky new syntax changes I will add because I'm an awkward fuck

This module contains:
- `Button` \[x1\]
- `Buzzer` \[x3\]
- `LCD` \[x1\]

Wiring:
- `1:` `+`
- `2:` `[LCD] +`
- `3:` `[LCD] SDA`
- `5:` `[LCD] SCL`
- `6:` `-`
- `13:` `[BZR] (MID) + `
- `15:` `[BZR] (HGH) +`
- `16:` `[BTN] (PWR) +`
- `18:` `[BZR] (LOW) +`

---------

### [**Button**](button.py) \[ID:1\]

_[Confused?](https://ktane.fandom.com/wiki/The_Button)_

This is one of the most basic modules, and the very first to be made (after the timer). It does what it says on the tin; there's a button that you have to press. However, you do have to follow certain rules for it to be defused correctly

The entire logic of this module has not been finished, however it is still defusable 
> _"I'm a dumbass lazy-ass bitch"_ 
> 
> The full button logic might not be ready for another decade at least :D

This module contains:
- `Button` \[x1\]
- `RGB LED` \[x1\]

Wiring:
- `1:` `+`
- `6:` `-`
- `11:` `[RGB] (RED) +`
- `13:` `[RGB] (GRN) +`
- `15:` `[RGB] (BLU) +`
- `16:` `[BTN] +`

References:
- `ID: 0` [Timer](https://github.com/dedlyT/ktane/blob/main/README.md#timer-id0)

---------
