# USB Theft Detection System

## Project Overview

The USB Theft Detection System is a Python-based security tool that monitors USB device connections to protect against unauthorized data transfer and potential data theft. The system detects when USB storage devices are connected to a computer, verifies if they are authorized, and sends email alerts when unauthorized devices are detected.

## Features

- **Real-time USB device monitoring**: Continuously scans for USB device connections
- **Authorization verification**: Checks connected devices against an authorized device database
- **Email alerts**: Sends immediate notifications when unauthorized devices are detected
- **Device management**: Add/remove devices from the authorized list
- **Detailed logging**: Records all USB connection events with timestamps
- **Cross-platform support**: Works on Windows, macOS, and Linux

## Installation Requirements

### Dependencies

```
pip install pandas
```

No additional external libraries are required beyond the Python standard library.

### System Requirements

- Python 3.6 or newer
- Email account for sending alerts (Gmail recommended)
- Administrative privileges may be required to detect USB devices

## Setup Instructions

1. **Create the authorized USB database**
   - Run the script and choose option to create a sample database
   - OR create own CSV file following the format in the documentation

2. **Configure email settings**
   - Set up an email account for sending alerts
   - For Gmail, create an App Password (not your regular password)
   - Enter SMTP settings in the configuration menu

3. **Run the monitoring system**
   - Start the monitoring service to detect USB devices
   - The system will check connected devices against the authorized list

## Usage Guide

### Starting the Program

```
python usb_authorization_detection.py
```

### Main Menu Options

1. **Start USB monitoring**
   - Begins real-time detection of USB devices
   - Runs continuously until stopped with Ctrl+C

2. **List authorized devices**
   - Displays all devices in the authorized database

3. **Add current USB device to authorized list**
   - Detects currently connected devices
   - Adds selected device to the authorized list

4. **Configure email alerts**
   - Set up email notifications for security alerts

5. **Exit**
   - Close the application

### Email Alert Configuration

To receive email alerts, you need to configure the following:
- SMTP server (e.g., smtp.gmail.com)
- SMTP port (e.g., 587 for TLS)
- Sender email address
- Sender password/app password
- Recipient email address for alerts

## Troubleshooting

### Common Issues

1. **USB devices not detected**
   - Ensure the script is running with administrative privileges
   - Check if the USB is properly connected
   - Try disconnecting and reconnecting the device

2. **Email alerts not working**
   - Verify SMTP server settings
   - For Gmail, make sure you're using an App Password
   - Check firewall settings that might block SMTP

3. **False positives**
   - Update the authorized devices list with all company-approved USB devices
   - Consider adding metadata like serial numbers to improve device identification

## Future Enhancements

- Automatic blocking of unauthorized devices
- Web-based dashboard for monitoring and administration
- Integration with enterprise security systems
- Machine learning for anomaly detection in USB usage patterns
- Mobile notifications for security alerts

## License

This project is provided for educational and security purposes. Use responsibly and in compliance with your organization's security policies.
