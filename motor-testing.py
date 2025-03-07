import pyvisa
import time
import csv
import matplotlib.pyplot as plt

# Initialize the VISA resource manager
rm = pyvisa.ResourceManager()

# Replace with the actual VISA address of your SPD1305X
instr_address = "USB0::62700::5136::SPD13ECD801362\x00\x00\x00\x00::0::INSTR"  # Update as needed
psu = rm.open_resource(instr_address)

# Set initial parameters
start_voltage = 4.2  # Starting voltage
end_voltage = 0.0    # Lowest voltage to reach
step = 0.1           # Voltage step size
delay = 0.1         # Decrease interval (seconds)
current_limit = 5.0  # Set current limit

# Set initial voltage and current limit
psu.write(f"CH1:VOLTage {start_voltage}")
psu.write(f"CH1:CURRent {current_limit}")

# File names for logging data
csv_filename = "voltage_current_power_log.csv"
txt_filename = "voltage_current_power_log.txt"

# Lists for graphing
time_values = []
voltage_values = []
current_values = []
power_values = []
try:
    # Open files for logging
    with open(csv_filename, mode="w", newline="") as csv_file, open(txt_filename, mode="w") as txt_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Time (s)", "Voltage (V)", "Current (A)", "Power (W)"])  # CSV Header
        txt_file.write("Time (s), Voltage (V), Current (A), Power (W)\n")  # TXT Header

        # Start the voltage decrement loop
        current_voltage = start_voltage
        start_time = time.time()
        psu.write("OUTPut CH1,ON")
        while current_voltage >= end_voltage:
            for i in range(10):
                # Measure voltage, current, and power
                measured_voltage = float(psu.query("MEASure:VOLTage? CH1").strip())
                measured_current = float(psu.query("MEASure:CURRent? CH1").strip())
                measured_power = float(psu.query("MEASure:POWEr? CH1").strip())
                elapsed_time = round(time.time() - start_time, 3)

                # Print and log the data
                print(f"[{elapsed_time}s] Voltage: {measured_voltage} V, Current: {measured_current} A, Power: {measured_power} W")

                # Write to CSV and TXT files
                csv_writer.writerow([elapsed_time, measured_voltage, measured_current, measured_power])
                txt_file.write(f"{elapsed_time}, {measured_voltage}, {measured_current}, {measured_power}\n")

                # Store data for graphing
                time_values.append(elapsed_time)
                voltage_values.append(measured_voltage)
                current_values.append(measured_current)
                power_values.append(measured_power)

                psu.write(f"CH1:VOLTage {current_voltage}")

                # Wait before next step
                #time.sleep(delay)
            # Decrease voltage
            current_voltage -= step
finally:
    psu.write("OUTPut CH1,OFF")
    # Close connection
    psu.close()

# Plot Voltage, Current, and Power over Time
plt.figure(figsize=(10, 6))

plt.subplot(3, 1, 1)
plt.plot(time_values, voltage_values, label="Voltage (V)", color="blue")
plt.ylabel("Voltage (V)")
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(time_values, current_values, label="Current (A)", color="red")
plt.ylabel("Current (A)")
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(time_values, power_values, label="Power (W)", color="green")
plt.xlabel("Time (s)")
plt.ylabel("Power (W)")
plt.legend()

plt.tight_layout()
plt.savefig("voltage_current_power_graph.png")  # Save the graph as an image
plt.show()

print(f"\nData recorded in {csv_filename} and {txt_filename}")
print("Graph saved as voltage_current_power_graph.png")