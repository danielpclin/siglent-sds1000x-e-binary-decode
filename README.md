siglent-sds1000x-e-binary-decode
================

Converts binary files exported from the *Siglent SDS-1000X-E* series oscilloscope into the Sigrok zip format (.sr).
This allows you to view and decode the waveforms in [PulseView](https://sigrok.org/wiki/PulseView).


Usage
======
    usage: decode.py [-h] [-r] [-v] filename
    
    positional arguments:
      filename       binary file to decode
    
    options:
      -h, --help     show this help message and exit
      -r, --raw      write to raw binary file instead of sigrok zip file
      -v, --verbose  print verbose logs
