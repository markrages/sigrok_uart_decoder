Decode a UART stream out of a Sigrok state file.

This is functionally equivalent to something like

   `sigrok-cli -i input.sr -P uart:rx=15:baudrate=9000000 -B uart=rx > output.bin`

But it is much, much faster, because the Sigrok analyzers are written in Python, whereas this script is written in Python.

Example comparison:

```lang=sh

time ./sigrok_uart_decode.py ~/tmp/input.sr --baudrate=9000000 --channel=15 ~/tmp/output.bin
logic-1-1/logic-1-477  Framing Error 206
Framing Error 313
logic-1-477/logic-1-477

real   0m5.578s
user   0m5.254s
sys    0m0.304s

time sigrok-cli -i  ~/tmp/input.sr -P uart:rx=15:baudrate=9000000 -B uart=rx > ~/tmp/output2.bin

real   26m46.850s
user   26m6.017s
sys    0m39.810s
```

Hints:

 - Record the stream with pulseview, not sigrok-cli.  The .sr format is very slow to write and sigrok-cli is single-threaded, so it will fail when the writing starves the reading of bandwidth.

 - pypy speeds the script up a lot.  Pypy packaging for Ubuntu is chaos (A snap? Really?) so this script is written for both Python 2 and 3 and uses only the "included batteries" to avoid dependency hell.

 - I've only used the script with my Saleae Logic16.  It might need some tweaking for other logic analysis sources.
