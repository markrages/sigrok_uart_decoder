#!/usr/bin/pypy

"""Decode a UART stream out of a Sigrok state file.

This is functionally equivalent to something like

   sigrok-cli -i input.sr -P uart:rx=15:baudrate=9000000 -B uart=rx > output.bin

But it is much, much faster, because the Sigrok analyzers are written in Python, whereas this script is written in Python.

Example comparison:

   time ./sigrok_uart_decode.py ~/tmp/input.sr --baudrate=9000000 --channel=15 ~/tmp/output.bin
   logic-1-1/logic-1-477  Framing Error 206
   Framing Error 313
   logic-1-477/logic-1-477

   real	   0m5.578s
   user	   0m5.254s
   sys	   0m0.304s

   time sigrok-cli -i  ~/tmp/input.sr -P uart:rx=15:baudrate=9000000 -B uart=rx > ~/tmp/output2.bin

   real	   26m46.850s
   user	   26m6.017s
   sys	   0m39.810s

Hints:

Record the stream with pulseview, not sigrok-cli.  The .sr format is very slow to write and sigrok-cli is single-threaded, so it will fail when the writing starves the reading of bandwidth.

pypy speeds the script up a lot.  Pypy packaging for Ubuntu is chaos (A snap? Really?) so this script is written for both Python 2 and 3 and uses only the "included batteries" to avoid dependency hell.

I've only used the script with my Saleae Logic16.  It might need some tweaking for other logic analysis sources.
"""

from __future__ import print_function

import sys,zipfile,io,array

try:
    import configparser
except ImportError:
    # Python 2.x fallback
    import ConfigParser as configparser

def decode_uart(filename, baudrate, channel=15):
    """ Decodes Sigrok (*.sr) file from logic16 capture.

    Returns a Bytes object.
    """

    with zipfile.ZipFile(sys.argv[1], 'r') as cr:

        a = cr.open('metadata')
        b = io.TextIOWrapper(a)
        #print(repr(b.read()))
        metadata = configparser.ConfigParser()
        metadata.readfp(b, 'metadata')
        samplerate = metadata.get('device 1', 'samplerate')
        samplerate = samplerate.replace(' MHz', 'e6')
        samplerate = samplerate.replace(' kHz', 'e3')
        samplerate = samplerate.replace(' Hz', 'e0')
        samplerate = float(samplerate)

        capturefile = metadata.get('device 1', 'capturefile')
        unitsize = metadata.get('device 1', 'unitsize')

        capturenames = [name for name in cr.namelist() if name.startswith(capturefile)]

        outbytes=[]

        skip = samplerate / baudrate
        # offsets from leading edge of start bit to middle of eight data
        # bits and stop bit.
        indexes = [1.5*skip, 2.5*skip, 3.5*skip, 4.5*skip,
                   5.5*skip, 6.5*skip, 7.5*skip, 8.5*skip,
                   9.5*skip]

        # When we get this many from end, load more data.
        spare_room = int(10*skip)

        indexes = [int(i) for i in indexes]
        rump = array.array('H')

        mask = 1<<channel

        for name in capturenames:
            sys.stdout.write("\r%s/%s  "%(name, capturenames[-1]))
            sys.stdout.flush()

            data = rump+array.array('H',cr.read(name, b'r'))
            lendata = len(data)
            index = 0

            while 1:
                if index > lendata - spare_room:
                    rump = data[index:]
                    break

                d = data[index] & mask
                if d==0: # start bit!
                    byte = 0
                    for bit in range(8):
                        byte >>= 1
                        if data[indexes[bit]+index] & mask:
                            byte |= 0x80

                    index += indexes[8]
                    if data[index] & mask == 0:
                        print("Framing Error", index)

                    while data[index] & mask ==0:
                        index += 1
                        if index > lendata - spare_room:
                            rump = data[index:]
                            break

                    else:
                        outbytes.append(byte)
                else:
                    index += 1

        print()
        return array.array('B', outbytes).tostring()

import argparse

parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])

parser.add_argument('--baudrate', type=int, help='Baudrate of stream', required=True)
parser.add_argument('--channel', type=int, help='Channel number (0-15)', required=True)
parser.add_argument('input', metavar='input.sr', nargs=1)
parser.add_argument('output', metavar='output.bin', nargs=1)

if __name__=="__main__":
    args = parser.parse_args()

    b = decode_uart(args.input[0],
                    args.baudrate,
                    args.channel)

    open(args.output[0],'wb').write(b)
