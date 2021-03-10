# Toontown OTP

OTP server implementation originally from AnythingTechPro with adaptions for a 2013 Toontown source.

### Dependencies
****ATTENTION!*** If you already downloaded the Panda3D version for AI/Districts on the Toontown repository skip downloading this.*

You will need a special Panda3D version, which you can get [here]() 
----
Execute the following script to install the missing modules for the server:
```sh
path\to\otp\python\ppython.exe -m pip install coloredlogs, semidbm, simplejson, pyyaml, pytoml
```

## Running the server
In order to run the server, if you wish, create a BAT file to automate the process:
```sh
@echo off
path\to\otp\python\ppython.exe -m realtime.main
pause
```

Voila! Next run the AI, then the game. Good luck!
