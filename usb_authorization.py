#!/usr/bin/python3
import csv
import os
import platform
import re
import smtplib
import subprocess
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class USBAuthorizationSystem:
    def __init__(self, authorized_usb_csv):
        self.authorized_usb_csv = authorized_usb_csv
        self.authorized_devices = self.load_authorized_devices()
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'kanishkaarde99@gmail.com',  # Update with your email
            'sender_password': 'bole utgq yawu rmga',  # Update with your app password
            'recipient_email': 'kanishkaarde99@gmail.com'  # Update with recipient email
        }
        
    def load_authorized_devices(self):
        """Load authorized USB devices from CSV file"""
        authorized_devices = []
        
        try:
            with open(self.authorized_usb_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    authorized_devices.append({
                        'vendor_id': row['vendor_id'].lower(),
                        'product_id': row['product_id'].lower(),
                        'serial_number': row['serial_number'],
                        'manufacturer': row['manufacturer'],
                        'product_name': row['product_name']
                    })
            print(f"Loaded {len(authorized_devices)} authorized devices")
            return authorized_devices
        except Exception as e:
            print(f"Error loading authorized devices: {e}")
            return []
    
    def get_connected_usb_devices(self):
        """Get a list of currently connected USB devices"""
        connected_devices = []
        
        if platform.system() == 'Windows':
            # Windows-specific USB detection using PowerShell
            ps_command = "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match '^USB' } | Select-Object -Property FriendlyName, InstanceId, DeviceID | ConvertTo-Json"
            process = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            
            if process.returncode == 0 and process.stdout.strip():
                import json
                
                # Handle both single device and multiple devices
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
                            
                            connected_devices.append({
                                'vendor_id': vendor_id,
                                'product_id': product_id,
                                'device_name': friendly_name,
                                'device_id': device_id,
                                'instance_id': instance_id
                            })
                except json.JSONDecodeError:
                    print("Error parsing PowerShell output")
        
        elif platform.system() == 'Linux':
            # Linux-specific USB detection using lsusb
            process = subprocess.run(['lsusb'], capture_output=True, text=True)
            
            if process.returncode == 0:
                lines = process.stdout.strip().split('\n')
                
                for line in lines:
                    # Example line: Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
                    match = re.search(r'ID (\w+):(\w+)', line)
                    if match:
                        vendor_id = match.group(1).lower()
                        product_id = match.group(2).lower()
                        
                        # Extract device name if present
                        device_name = line.split(f"ID {vendor_id}:{product_id}")[-1].strip()
                        if not device_name:
                            device_name = "Unknown USB Device"
                        
                        connected_devices.append({
                            'vendor_id': vendor_id,
                            'product_id': product_id,
                            'device_name': device_name,
                            'device_id': f"{vendor_id}:{product_id}"
                        })
        
        elif platform.system() == 'Darwin':  # macOS
            # macOS-specific USB detection using system_profiler
            process = subprocess.run(['system_profiler', 'SPUSBDataType'], capture_output=True, text=True)
            
            if process.returncode == 0:
                output = process.stdout
                
                # Extract USB device information
                vendor_id_matches = re.finditer(r'Vendor ID: (0x[0-9a-fA-F]+)', output)
                product_id_matches = re.finditer(r'Product ID: (0x[0-9a-fA-F]+)', output)
                manufacturer_matches = re.finditer(r'Manufacturer: (.+)', output)
                product_matches = re.finditer(r'Product: (.+)', output)
                
                # Combine the matches
                vendor_ids = [m.group(1)[2:].lower() for m in vendor_id_matches]
                product_ids = [m.group(1)[2:].lower() for m in product_id_matches]
                manufacturers = [m.group(1) for m in manufacturer_matches]
                products = [m.group(1) for m in product_matches]
                
                # Create device dictionaries
                for i in range(min(len(vendor_ids), len(product_ids))):
                    manufacturer = manufacturers[i] if i < len(manufacturers) else "Unknown"
                    product = products[i] if i < len(products) else "Unknown"
                    
                    connected_devices.append({
                        'vendor_id': vendor_ids[i],
                        'product_id': product_ids[i],
                        'device_name': f"{manufacturer} {product}",
                        'device_id': f"{vendor_ids[i]}:{product_ids[i]}"
                    })
        
        return connected_devices
    
    def is_device_authorized(self, device):
        """Check if a device is in the authorized list"""
        for auth_device in self.authorized_devices:
            if (device['vendor_id'] == auth_device['vendor_id'].lower() and 
                device['product_id'] == auth_device['product_id'].lower()):
                return True
        return False
    
    def send_email_alert(self, unauthorized_device):
        """Send an email alert about unauthorized USB device"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            msg['Subject'] = 'SECURITY ALERT: Unauthorized USB Device Detected'
            
            # Create message body
            body = f"""
            <html>
              <body>
                <h2>⚠️ Security Alert: Unauthorized USB Device Detected</h2>
                <p>An unauthorized USB device has been connected to your system.</p>
                <h3>Device Details:</h3>
                <ul>
                  <li><strong>Vendor ID:</strong> {unauthorized_device['vendor_id']}</li>
                  <li><strong>Product ID:</strong> {unauthorized_device['product_id']}</li>
                  <li><strong>Device Name:</strong> {unauthorized_device['device_name']}</li>
                  <li><strong>Detection Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                  <li><strong>System:</strong> {platform.node()}</li>
                </ul>
                <p>Please investigate this security incident immediately.</p>
                <p><i>This is an automated message from your USB Authorization System.</i></p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent for unauthorized device: {unauthorized_device['device_name']}")
            return True
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
    
    def log_unauthorized_device(self, device):
        """Log unauthorized device to a file"""
        try:
            with open('unauthorized_usb_log.csv', 'a', newline='') as f:
                # Create header if file is empty
                if os.path.getsize('unauthorized_usb_log.csv') == 0:
                    fieldnames = ['timestamp', 'vendor_id', 'product_id', 'device_name', 'system', 'user']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                else:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'vendor_id', 'product_id', 'device_name', 'system', 'user'])
                
                writer.writerow({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'vendor_id': device['vendor_id'],
                    'product_id': device['product_id'],
                    'device_name': device['device_name'],
                    'system': platform.node(),
                    'user': os.getlogin()
                })
            print(f"Logged unauthorized device: {device['device_name']}")
            return True
        except Exception as e:
            print(f"Error logging unauthorized device: {e}")
            return False
    
    def monitor_usb_devices(self, check_interval=5):
        """Monitor for USB devices at specified interval"""
        print(f"Starting USB monitoring (check interval: {check_interval} seconds)")
        print(f"System: {platform.system()} {platform.release()}")
        print("Press Ctrl+C to stop monitoring")
        
        # Track detected devices to avoid duplicate alerts
        detected_devices = set()
        
        try:
            while True:
                connected_devices = self.get_connected_usb_devices()
                
                for device in connected_devices:
                    device_key = f"{device['vendor_id']}:{device['product_id']}"
                    
                    # Only process new devices that haven't been detected before
                    if device_key not in detected_devices:
                        # Check if device is authorized
                        is_authorized = self.is_device_authorized(device)
                        
                        if is_authorized:
                            print(f"✓ AUTHORIZED: USB device detected: {device['device_name']} ({device_key})")
                        else:
                            print(f"⚠️ ALERT: Unauthorized USB device detected: {device['device_name']} ({device_key})")
                            # Log the unauthorized device
                            self.log_unauthorized_device(device)
                            # Send email alert
                            self.send_email_alert(device)
                        
                        # Add to detected set to avoid duplicate alerts
                        detected_devices.add(device_key)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\nUSB monitoring stopped by user")
        except Exception as e:
            print(f"Error in USB monitoring: {e}")

def main():
    # Check for arguments
    if len(sys.argv) < 2:
        print("Usage: python usb_authorization.py <authorized_usb_csv>")
        sys.exit(1)

    authorized_usb_csv = sys.argv[1]
    
    # Check if the CSV file exists
    if not os.path.isfile(authorized_usb_csv):
        print(f"Error: Authorized USB CSV file '{authorized_usb_csv}' not found.")
        sys.exit(1)
    
    # Initialize and run the USB authorization system
    usb_system = USBAuthorizationSystem(authorized_usb_csv)
    usb_system.monitor_usb_devices()

if __name__ == "__main__":
    main()





