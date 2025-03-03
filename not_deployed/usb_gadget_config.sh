#!/bin/bash
set -e  # Exit immediately if a command fails

# Load required module
modprobe libcomposite

# Create and mount configfs if not already mounted
mkdir -p /config
mount -t configfs none /config || true

# Create USB gadget directory
mkdir -p /config/usb_gadget/usb_net
cd /config/usb_gadget/usb_net

# Set USB Vendor and Product ID
echo 0x1d6b > idVendor
echo 0x0104 > idProduct

# Set device strings
mkdir -p strings/0x409
echo "123456789" > strings/0x409/serialnumber
echo "Texas Instruments" > strings/0x409/manufacturer
echo "AM62 USB Network" > strings/0x409/product

# Create Ethernet function
mkdir -p functions/ecm.0

# Set a **static** MAC address for consistency
echo "42:ea:74:d2:92:37" > functions/ecm.0/dev_addr  # Device MAC
echo "42:ea:74:d2:92:38" > functions/ecm.0/host_addr # Host MAC

# Create USB gadget configuration
mkdir -p configs/c.1
mkdir -p configs/c.1/strings/0x409
echo "USB Ethernet Config" > configs/c.1/strings/0x409/configuration
ln -s functions/ecm.0 configs/c.1/

# Enable the USB gadget
echo 31000000.usb > UDC

# Assign static IP to USB interface
#echo "Configuring USB0 interface..."
#ip addr add 192.168.2.2/24 dev usb0
#ip link set usb0 up

# Wait for the USB interface to appear before assigning an IP
echo "Waiting for USB0 to be available..."
while ! ip link show usb0 > /dev/null 2>&1; do
    sleep 1
done

# Assign static IP to USB interface
echo "Configuring USB0 interface..."
ip addr add 192.168.2.2/24 dev usb0
ip link set usb0 up


echo "USB Ethernet Gadget Setup Complete"