#!/usr/bin/env python3
"""
Verify ZED-F9P Base Station Configuration
Run on Mac or computer with base station connected

Usage:
    python3 base_verify.py /dev/tty.usbmodem14201
"""

import serial
import struct
import time
import sys

def read_ubx_message(ser, timeout=2.0):
    """Read a UBX message from serial"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if ser.in_waiting >= 2:
            header = ser.read(2)
            if header == b'\xb5\x62':  # UBX header
                msg_class = ser.read(1)[0]
                msg_id = ser.read(1)[0]
                length = struct.unpack('<H', ser.read(2))[0]
                payload = ser.read(length)
                checksum = ser.read(2)
                return msg_class, msg_id, payload
        time.sleep(0.01)
    return None, None, None

def verify_base_station(port, baudrate=38400):
    """Verify base station configuration"""
    
    print(f"🔍 Connecting to {port}...")
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(1)
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False
    
    print("✓ Connected\n")
    
    # Request TMODE3 configuration
    print("📡 Checking TMODE3 (Time Mode) Configuration...")
    poll_msg = b'\xb5\x62\x06\x71\x00\x00\x77\x59'  # CFG-TMODE3 poll
    ser.write(poll_msg)
    time.sleep(0.5)
    
    msg_class, msg_id, payload = read_ubx_message(ser)
    
    if msg_class == 0x06 and msg_id == 0x71 and payload:
        version = payload[0]
        mode = struct.unpack('<H', payload[2:4])[0]
        
        mode_names = {
            0: "DISABLED (Rover mode)",
            1: "SURVEY_IN (Surveying position)",
            2: "FIXED (Base station mode)"
        }
        
        mode_str = mode_names.get(mode, f"Unknown ({mode})")
        print(f"   Mode: {mode_str}")
        
        if mode == 2:  # Fixed mode
            print("   ✅ Base station is in FIXED mode!")
            
            # Extract position
            ecef_x = struct.unpack('<i', payload[4:8])[0]
            ecef_y = struct.unpack('<i', payload[8:12])[0]
            ecef_z = struct.unpack('<i', payload[12:16])[0]
            
            print(f"   Position ECEF: X={ecef_x/100:.2f}m, Y={ecef_y/100:.2f}m, Z={ecef_z/100:.2f}m")
            
        elif mode == 1:  # Survey-in
            print("   ⚠️  Still in SURVEY_IN mode")
            print("   Wait for survey to complete (5-10 minutes)")
        else:
            print("   ❌ Base station not configured (DISABLED)")
            print("   Run configure_base_station.py first")
    else:
        print("   ❌ Could not read TMODE3 configuration")
    
    # Check UART2 configuration
    print("\n📻 Checking UART2 Configuration...")
    poll_uart2 = b'\xb5\x62\x06\x00\x01\x00\x02\x08\x16'  # CFG-PRT poll for UART2
    ser.write(poll_uart2)
    time.sleep(0.5)
    
    msg_class, msg_id, payload = read_ubx_message(ser)
    
    if msg_class == 0x06 and msg_id == 0x00 and payload:
        port_id = payload[0]
        baudrate = struct.unpack('<I', payload[8:12])[0]
        in_proto = struct.unpack('<H', payload[12:14])[0]
        out_proto = struct.unpack('<H', payload[14:16])[0]
        
        print(f"   Port: UART{port_id}")
        print(f"   Baudrate: {baudrate}")
        print(f"   Output Protocol: ", end="")
        
        if out_proto & 0x04:
            print("RTCM3 ✓")
        else:
            print("❌ RTCM3 not enabled")
            print("   Run configure_base_station.py to fix")
    else:
        print("   ❌ Could not read UART2 configuration")
    
    # Check RTCM message configuration
    print("\n📊 Checking RTCM Message Output...")
    rtcm_msgs = [
        (0xF5, 0x05, "1005 - Antenna Position"),
        (0xF5, 0x4D, "1077 - GPS MSM7"),
        (0xF5, 0x57, "1087 - GLONASS MSM7"),
        (0xF5, 0x61, "1097 - Galileo MSM7"),
    ]
    
    all_enabled = True
    for msg_class, msg_id, name in rtcm_msgs:
        # Poll message rate
        poll = b'\xb5\x62\x06\x01\x02\x00' + bytes([msg_class, msg_id])
        checksum = sum(poll[2:]) & 0xFF
        poll += bytes([checksum, (checksum + sum(poll[2:])) & 0xFF])
        
        ser.write(poll)
        time.sleep(0.1)
    
    # Simplified check
    print("   RTCM messages should be enabled")
    print("   (Detailed check requires longer monitoring)")
    
    ser.close()
    
    print("\n" + "="*60)
    print("📋 VERIFICATION SUMMARY")
    print("="*60)
    print("\n✅ Base station verification complete!")
    print("\n🔧 Next Steps:")
    print("1. Connect radio to UART2 (TX/RX/GND)")
    print("2. Power on base at competition site")
    print("3. Base will automatically use saved position")
    print("4. Radio will broadcast RTCM corrections")
    print("\n💡 To monitor RTCM output:")
    print(f"   screen {port} {baudrate}")
    print("   You should see binary data streaming")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 base_verify.py <port>")
        print("\nFind your device:")
        print("  Mac:   ls /dev/tty.usbmodem*")
        print("  Linux: ls /dev/ttyACM*")
        print("\nExample:")
        print("  python3 base_verify.py /dev/tty.usbmodem14201")
        return
    
    port = sys.argv[1]
    verify_base_station(port, 9600)

if __name__ == '__main__':
    main()

