## Audio Incident

- Timestamp: 2026-07-18T20:14:10Z
- Classification: device_disconnect (0.92)
- Likely Cause: USB bus reset while audio interface was active

### Evidence
- 2026-07-18T20:14:09Z [com.apple.iokit.usb] Port reset on external hub
- 2026-07-18T20:14:10Z [coreaudiod] HALS_IOA1Engine.cpp: output stream stopped

### Raw Context
coreaudiod: Audio device removed while active output stream in Logic Pro.
