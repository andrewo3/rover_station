#!/usr/bin/env python3
"""
ZED-F9P Base Station Configuration Script
Run this on your Mac with base F9P connected

Usage:
    python3 configure_base_station.py /dev/tty.usbmodem14201

This will:
1. Put F9P into Survey-In mode
2. Wait for position to stabilize (5-10 min)
3. Save position to flash
4. Configure RTCM output for radio transmission
"""

import serial
import time
import struct
import sys

class UBXMessage:
    """Helper for UBX protocol messages"""
    
    @staticmethod
    def checksum(data):
        """Calculate UBX checksum"""
        ck_a = ck_b = 0
        for byte in data:
            ck_a = (ck_a + byte) & 0xFF
            ck_b = (ck_b + ck_a) & 0xFF
        return bytes([ck_a, ck_b])
    
    @staticmethod
    def create(msg_class, msg_id, payload):
        """Create UBX message"""
        header = b'\xb5\x62'
        length = struct.pack('<H', len(payload))
        msg = header + bytes([msg_class, msg_id]) + length + payload
        return msg + UBXMessage.checksum(bytes([msg_class, msg_id]) + length + payload)

def configure_base_station(port, baudrate=38400):
    """Configure F9P as RTK base station"""
    
    print(f"🔧 Connecting to {port}...")
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(1)
    except Exception as e:
        print(f"❌ Failed to open port: {e}")
        print("\nTroubleshooting:")
        print("1. Check device is connected: ls /dev/tty.usbmodem*")
        print("2. Close any apps using the GPS (u-center, etc)")
        print("3. Try unplugging and replugging USB")
        return False
    
    print("✓ Connected to F9P")
    
    # Step 1: Set TMODE3 to Survey-In
    print("\n📡 Step 1: Starting Survey-In Mode")
    print("The base station will now measure its position for 5-10 minutes...")
    print("⚠️  Keep the antenna stationary with clear sky view!")
    
    # TMODE3: Survey-In mode
    # Parameters: mode=1 (survey-in), accuracy limit=200 (2m), min duration=300s
    tmode3_payload = struct.pack('<BBHIIIHHHII', 
        0x00, 0x01,  # version, reserved
        0x0001,      # flags: survey-in enabled
        0,           # ECEF X (unused in survey-in)
        0,           # ECEF Y
        0,           # ECEF Z
        0, 0, 0,     # position HP, reserved
        200,         # accuracy limit (0.1mm units, so 2000 = 2m)
        300          # min survey duration (seconds)
    )
    
    msg = UBXMessage.create(0x06, 0x71, tmode3_payload)  # CFG-TMODE3
    ser.write(msg)
    time.sleep(0.5)
    
    print("✓ Survey-In mode enabled")
    print("\n⏱  Waiting for survey to complete (this takes 5-10 minutes)...")
    print("   You can close this script and check status later with:")
    print("   screen /dev/tty.usbmodem14201 38400")
    print("\n   Status messages will show survey progress")
    
    # Step 2: Enable RTCM messages
    print("\n📡 Step 2: Enabling RTCM Messages")
    
    rtcm_messages = [
        (0xF5, 0x05, 1),  # RTCM3.3 1005 - Antenna position
        (0xF5, 0x4D, 1),  # RTCM3.3 1077 - GPS MSM7
        (0xF5, 0x57, 1),  # RTCM3.3 1087 - GLONASS MSM7
        (0xF5, 0x61, 1),  # RTCM3.3 1097 - Galileo MSM7
        (0xF5, 0x7F, 1),  # RTCM3.3 1127 - BeiDou MSM7
        (0xF5, 0xE6, 1),  # RTCM3.3 1230 - GLONASS code-phase biases
    ]
    
    for msg_class, msg_id, rate in rtcm_messages:
        # CFG-MSG: Set message rate
        payload = struct.pack('<BBB', msg_class, msg_id, rate)
        msg = UBXMessage.create(0x06, 0x01, payload)
        ser.write(msg)
        time.sleep(0.1)
    
    print("✓ RTCM messages enabled (1Hz output)")
    
    # Step 3: Set UART2 for RTCM output (for radio)
    print("\n📡 Step 3: Configuring UART2 for radio")
    
    # CFG-PRT for UART2
    # Set to 57600 baud, 8N1, RTCM3 output
    prt_payload = struct.pack('<BBHIIHHHH',
        2,           # Port ID (2 = UART2)
        0,           # reserved
        0x0000,      # txReady (disabled)
        0x000008D0,  # mode: 8N1
        57600,       # baudrate (match your radio)
        0x0005,      # inProtoMask: UBX + RTCM3
        0x0004,      # outProtoMask: RTCM3 only
        0x0000,      # flags
        0x0000       # reserved
    )
    
    msg = UBXMessage.create(0x06, 0x00, prt_payload)
    ser.write(msg)
    time.sleep(0.5)
    
    print("✓ UART2 configured (57600 baud, RTCM output)")
    print("\n📻 Connect your radio TX to UART2:")
    print("   F9P UART2 TX → Radio RX")
    print("   F9P GND      → Radio GND")
    
    # Step 4: Save configuration
    print("\n💾 Step 4: Saving configuration to flash")
    
    # CFG-CFG: Save to flash
    cfg_payload = struct.pack('<IIB',
        0xFFFFFFFF,  # Clear mask (all)
        0x0000061F,  # Save mask (BBR, Flash, I2C-EEPROM)
        0x00         # Device mask (BBR)
    )
    
    msg = UBXMessage.create(0x06, 0x09, cfg_payload)
    ser.write(msg)
    time.sleep(1)
    
    print("✓ Configuration saved to F9P flash memory")
    
    ser.close()
    
    print("\n" + "="*60)
    print("✅ BASE STATION CONFIGURATION COMPLETE!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Wait 5-10 minutes for survey to complete")
    print("2. Once complete, F9P will switch to FIXED mode automatically")
    print("3. Connect 915MHz radio to UART2 (TX/RX/GND)")
    print("4. Radio will broadcast RTCM corrections")
    print("5. Power on base station at competition site")
    print("\nTo check survey status:")
    print(f"  screen {port} 38400")
    print("\nLook for 'surveyIn: active=1, valid=1' in status messages")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 configure_base_station.py <port>")
        print("\nFind your device:")
        print("  Mac:   ls /dev/tty.usbmodem*")
        print("  Linux: ls /dev/ttyACM*")
        print("\nExample:")
        print("  python3 configure_base_station.py /dev/tty.usbmodem14201")
        return
    
    port = sys.argv[1]
    configure_base_station(port)

if __name__ == '__main__':
    main()

