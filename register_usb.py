#!/usr/bin/python3
import csv
import os
import platform
import re
import subprocess
import sys
from datetime import datetime

def get_current_usb_devices():
    """Get currently connected USB devices"""
    connected_devices = []
    
    if platform.system() == 'Windows':
        # Windows-specific USB detection using PowerShell
        ps_command = "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match '^USB' } | Select-Object -Property FriendlyName, InstanceId, DeviceID | ConvertTo-Json"
        process = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
        
        if process.returncode == 0 and process.stdout.strip():
            import json
            
            try:
                devices_data = json.loads(process.stdout)
                # Make sure devices_data is a list
                if isinstance(devices_data, dict):
                    devices_data = [devices_data]
                    
                for device in devices_data:
                    # Extract VID and PID from device ID if available
                    device_id = device.get('DeviceID', '')
                    instance_id = device.get('InstanceId', '')
                    friendly_name = device.get('FriendlyName', 'Unknown Device')
                    
                    vid_match = re.search(r'VID_([0-9A-F]{4})', device_id)
                    pid_match = re.search(r'PID_([0-9A-F]{4})', device_id)
                    
                    if vid_match and pid_match:
                        vendor_id = vid_match.group(1).lower()
                        product_id = pid_match.group(1).lower()
                        
                        # Try to get serial number
                        serial_number = "Unknown"
                        sn_match = re.search(r'\\(.+)$', instance_id)
                        if sn_match:
                            serial_number = sn_match.group(1)
                        
                        connected_devices.append({
                            'vendor_id': vendor_id,
                            'product_id': product_id,
                            'serial_number': serial_number,
                            'manufacturer': friendly_name.split()[0] if ' ' in friendly_name else 'Unknown',
                            'product_name': friendly_name
                        })
            except json.JSONDecodeError:
                print("Error parsing PowerShell output")
    
    elif platform.system() == 'Linux':
        # Linux-specific USB detection
        process = subprocess.run(['lsusb'], capture_output=True, text=True)
        
        if process.returncode == 0:
            lines = process.stdout.strip().split('\n')
            
            for line in lines:
                # Example line: Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
                match = re.search(r'ID (\w+):(\w+) (.+)', line)
                if match:
                    vendor_id = match.group(1).lower()
                    product_id = match.group(2).lower()
                    device_name = match.group(3) if len(match.groups()) > 2 else "Unknown Device"
                    
                    # Try to extract manufacturer and product name
                    parts = device_name.split(' ', 1)
                    manufacturer = parts[0] if len(parts) > 0 else "Unknown"
                    product_name = parts[1] if len(parts) > 1 else device_name
                    
                    # Try to get serial number (this requires root)
                    serial_number = "Unknown"
                    try:
                        # This might require root privileges
                        serial_process = subprocess.run(
                            ['lsusb', '-v', '-d', f'{vendor_id}:{product_id}'], 
                            capture_output=True, 
                            text=True
                        )
                        if serial_process.returncode == 0:
                            sn_match = re.search(r'iSerial\s+\d+\s+(\S+)', serial_process.stdout)
                            if sn_match:
                                serial_number = sn_match.group(1)
                    except Exception:
                        pass
                    
                    connected_devices.append({
                        'vendor_id': vendor_id,
                        'product_id': product_id,
                        'serial_number': serial_number,
                        'manufacturer': manufacturer,
                        'product_name': product_name
                    })
    
    elif platform.system() == 'Darwin':  # macOS
        # macOS-specific USB detection
        process = subprocess.run(['system_profiler', 'SPUSBDataType'], capture_output=True, text=True)
        
        if process.returncode == 0:
            output = process.stdout
            
            # Parse the output for USB devices
            # This is simplified and may need refinement for macOS
            sections = output.split('\n\n')
            current_device = {}
            
            for section in sections:
                if 'Vendor ID:' in section:
                    # Extract vendor ID
                    vendor_match = re.search(r'Vendor ID: (0x[0-9a-fA-F]+)', section)
                    if vendor_match:
                        current_device['vendor_id'] = vendor_match.group(1)[2:].lower()
                    
                    # Extract product ID
                    product_match = re.search(r'Product ID: (0x[0-9a-fA-F]+)', section)
                    if product_match:
                        current_device['product_id'] = product_match.group(1)[2:].lower()
                    
                    # Extract manufacturer
                    manufacturer_match = re.search(r'Manufacturer: (.+)', section)
                    if manufacturer_match:
                        current_device['manufacturer'] = manufacturer_match.group(1)
                    else:
                        current_device['manufacturer'] = "Unknown"
                    
                    # Extract product name
                    product_name_match = re.search(r'Product: (.+)', section)
                    if product_name_match:
                        current_device['product_name'] = product_name_match.group(1)
                    else:
                        current_device['product_name'] = "Unknown Device"
                    
                    # Extract serial number
                    serial_match = re.search(r'Serial Number: (.+)', section)
                    if serial_match:
                        current_device['serial_number'] = serial_match.group(1)
                    else:
                        current_device['serial_number'] = "Unknown"
                    
                    # Only add if we have both vendor and product ID
                    if 'vendor_id' in current_device and 'product_id' in current_device:
                        connected_devices.append(current_device.copy())
                    current_device = {}
    
    return connected_devices

def add_device_to_authorized_list(device, csv_file, added_by="admin", department=""):
    """Add a device to the authorized USB list"""
    # Check if file exists and create with header if it doesn't
    file_exists = os.path.isfile(csv_file)
    
    fieldnames = ['vendor_id', 'product_id', 'serial_number', 'manufacturer', 
                  'product_name', 'date_added', 'added_by', 'department']
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Add current date
        device['date_added'] = datetime.now().strftime('%Y-%m-%d')
        device['added_by'] = added_by
        device['department'] = department
        
        writer.writerow(device)
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python register_usb.py <authorized_usb_csv>")
        sys.exit(1)
    
    authorized_usb_csv = sys.argv[1]
    
    print("USB Device Registration Tool")
    print("---------------------------")
    print(f"Authorized USB CSV: {authorized_usb_csv}")
    print("\nDetecting connected USB devices...\n")
    
    connected_devices = get_current_usb_devices()
    
    if not connected_devices:
        print("No USB devices detected. Please ensure USB devices are connected properly.")
        sys.exit(1)
    
    print(f"Found {len(connected_devices)} USB devices:")
    
    # Display devices
    for i, device in enumerate(connected_devices):
        print(f"\n{i+1}. {device.get('manufacturer', 'Unknown')} {device.get('product_name', 'Unknown Device')}")
        print(f"   VID: {device.get('vendor_id', 'Unknown')} | PID: {device.get('product_id', 'Unknown')}")
        print(f"   S/N: {device.get('serial_number', 'Unknown')}")
    
    # Ask which device to authorize
    try:
        choice = int(input("\nEnter the number of the device to authorize (0 to exit): "))
        if choice == 0:
            print("Exiting without changes.")
            sys.exit(0)
        
        if choice < 1 or choice > len(connected_devices):
            print("Invalid selection. Exiting.")
            sys.exit(1)
        
        selected_device = connected_devices[choice-1]
        
        # Ask for department
        department = input("Enter department for this device: ")
        
        # Ask for confirmation
        print("\nAbout to authorize the following device:")
        print(f"Manufacturer: {selected_device.get('manufacturer', 'Unknown')}")
        print(f"Product: {selected_device.get('product_name', 'Unknown')}")
        print(f"VID: {selected_device.get('vendor_id', 'Unknown')} | PID: {selected_device.get('product_id', 'Unknown')}")
        print(f"S/N: {selected_device.get('serial_number', 'Unknown')}")
        print(f"Department: {department}")
        
        confirm = input("\nAdd this device to the authorized list? (y/n): ")
        
        if confirm.lower() == 'y':
            selected_device['department'] = department
            if add_device_to_authorized_list(selected_device, authorized_usb_csv):
                print("\n✅ Device successfully added to authorized list!")
        else:
            print("\nOperation cancelled. No changes made.")
    
    except ValueError:
        print("Invalid input. Please enter a number.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

if __name__ == "__main__":
    main()