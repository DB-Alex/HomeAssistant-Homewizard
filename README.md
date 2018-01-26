# HomeAssistant-Homewizard
Homewizard Climate component for HomeAssistant

This component is experimental, since i don't have sufficient knowledge of Python yet to fully support it.
Use it at your own risk.

This component wouldn't be possible without the massive amount of inspiration I got from the following scripts:
https://github.com/cyberjunky/home-assistant-custom-components/blob/master/climate/toon.py
https://github.com/rvdvoorde/domoticz-homewizard

Add this to your configuration.yaml:
```
climate:
  - platform: homewizard
    name: Homewizard
    host: IP adress host
    password: Password
    # not sure if this works:
    scan_interval: 10
```

THen add the homewizard.py file to the config-folder/custom_components/climate and restart Home Assistant. 
