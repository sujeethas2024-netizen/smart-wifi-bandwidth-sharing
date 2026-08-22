@echo off
rem ============================================================
rem   ONE-TIME firewall setup (runs elevated via UAC prompt).
rem   Allows phones/laptops on the WiFi to reach the app.
rem ============================================================
netsh advfirewall firewall add rule name="SmartWiFi-5000" dir=in action=allow protocol=TCP localport=5000
exit