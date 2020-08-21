# MaximumRoverdrive

Uses pymavlink to monitor selected MAVLink messages and display them in a "sticky" window with a familiar theme.

Project is in its infancy and may not ever reach a fully releasable/stable version.  I simply wanted a way to monitor certain MAVLink messages in a cleanly formatted presentation without using a CLI.  It is close to providing all desired functionality, and once achieved, development will likely cease.

- [ ] TODO: test for stability
- [ ] TODO: send waypoint missions?
- [x] DONE: ~~Implement automatic headlights~~
- [x] DONE: ~~Add command send history to preferences in MAV.ini~~
- [x] DONE: ~~make the UI layout less clunky~~
- [x] DONE: ~~add mission start/end commands to WP files~~
- [x] DONE: ~~create an interface for sending messages (like toggling relays)~~
- [x] DONE: ~~finish config file IO (almost complete - need "remove" functionality)~~
- [x] DONE: ~~allow user selectable messages (instead of test input)~~
- [x] DONE: ~~allow user to set min/max values and multipliers for display formatting~~
- [x] DONE: ~~more efficient MAVlink message collection~~

Requires: pymavlink, PyQt5, configparser, watchdog, astral

_Should_ be cross-platform compatible, however only tested on Windows 10 in a Python 3.7 environment.

<br><hr>
<sup>Copyright (c) 2020 -- Yuri
<br><br>
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
<br><br>
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
<br><br>
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</sup>
