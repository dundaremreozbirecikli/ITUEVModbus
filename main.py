import serial
import time
import libscrc
import can
import os
import datetime

# Open the serial port and configure it
ser = serial.Serial()
ser.baudrate = 9600
ser.port = 'COM5'
ser.parity = 'N'
ser.stopbits = 2
ser.bytesize = 8
ser.timeout = 5
ser.open()

# Open the CANBUS protocol interface
bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)

# Define the data commands to be sent to the device
vol = [0x01, 0x04, 0x75, 0x46, 0x00, 0x02, 0x8A, 0x12]  # 0x7564
temp = [0x01, 0x04, 0x75, 0x4C, 0x00, 0x01, 0xEA, 0x11]  # 0x754C
soc_min = [0x01, 0x04, 0x75, 0x4D, 0x00, 0x02, 0xFB, 0xD0]  # 754D  adresi degisecek
min_cell_vol = [0x01, 0x04, 0x75, 0x4F, 0x00, 0x01, 0x1A, 0x11]  # 0x754F
max_cell_vol = [0x01, 0x04, 0x75, 0x50, 0x00, 0x01, 0x2B, 0xD7]  # 0x7550

# Read cell voltages Module 0-3
# cells = [[0x01, 0x04, 0x75, 0x6D, 0x00, 0x01, 0xBA, 0x1B], [0x01, 0x04, 0x75, 0x6F, 0x00, 0x01, 0x1B, 0xDB],
#         [0x01, 0x04, 0x75, 0x71, 0x00, 0x01, 0x7B, 0xDD], [0x01, 0x04, 0x75, 0x73, 0x00, 0x01, 0xDA, 0x1D],
#         [0x01, 0x04, 0x75, 0x75, 0x00, 0x01, 0x3A, 0x1C], [0x01, 0x04, 0x75, 0x77, 0x00, 0x01, 0x9B, 0xDC],
#         [0x01, 0x04, 0x75, 0x81, 0x00, 0x01, 0x7B, 0xEE], [0x01, 0x04, 0x75, 0x83, 0x00, 0x01, 0xDA, 0x2E],
#         [0x01, 0x04, 0x75, 0x85, 0x00, 0x01, 0x3A, 0x2F], [0x01, 0x04, 0x75, 0x87, 0x00, 0x01, 0x9B, 0xEF],
#         [0x01, 0x04, 0x75, 0x89, 0x00, 0x01, 0xFA, 0x2C], [0x01, 0x04, 0x75, 0x8B, 0x00, 0x01, 0x5B, 0xEC],
#         [0x01, 0x04, 0x75, 0x95, 0x00, 0x01, 0x3B, 0xEA], [0x01, 0x04, 0x75, 0x97, 0x00, 0x01, 0x9A, 0x2A],
#         [0x01, 0x04, 0x75, 0x99, 0x00, 0x01, 0xFB, 0xE9], [0x01, 0x04, 0x75, 0x9B, 0x00, 0x01, 0x5A, 0x29],
#         [0x01, 0x04, 0x75, 0x9D, 0x00, 0x01, 0xBA, 0x28], [0x01, 0x04, 0x75, 0x9F, 0x00, 0x01, 0x1B, 0xE8],
#         [0x01, 0x04, 0x75, 0xA9, 0x00, 0x01, 0xFB, 0xE6], [0x01, 0x04, 0x75, 0xAB, 0x00, 0x01, 0x5A, 0x26],
#         [0x01, 0x04, 0x75, 0xAD, 0x00, 0x01, 0xBA, 0x27], [0x01, 0x04, 0x75, 0xAF, 0x00, 0x01, 0x1B, 0xE7],
#         [0x01, 0x04, 0x75, 0xB1, 0x00, 0x01, 0x7B, 0xE1], [0x01, 0x04, 0x75, 0xB3, 0x00, 0x01, 0xDA, 0x21]]

# cells = [0x01, 0x04, 0x75, 0x6D, 0x00, 0x2F, 0x3A, 0x07]

cells = [0x01, 0x04, 0x75, 0x6D, 0x00, 0x0C, 0x7B, 0xDE]


# Define a function to compute the CRC checksum of a message
def crc16(data: bytes):
    crc = 0xffff
    for cur_byte in data:
        crc = crc ^ cur_byte
        for _ in range(8):
            a = crc
            carry_flag = a & 0x0001
            crc = crc >> 1
            if carry_flag == 1:
                crc = crc ^ 0xa001
    return bytes([crc % 256, crc >> 8 % 256])


def findsoc(input_voltage, min_voltage, max_voltage):
    soc = (input_voltage - min_voltage) / (max_voltage - min_voltage) * 100
    if soc > 100:
        soc = 100
    elif soc < 0:
        soc = 0
    return round(soc, 2)


# Open the file for writing
with open("/path/to/microSD/values.txt", 'w') as file:
    # Loop indefinitely to retrieve data from the device
    while True:
        # Request and receive the state of voltage data
        time.sleep(1)
        ser.write(vol)
        time.sleep(2)
        bytesToRead_vol = ser.inWaiting()
        response_vol = ser.read(bytesToRead_vol)
        print(response_vol)
        response_vol_decoded = libscrc.modbus(response_vol)
        if len(response_vol) >= 6:
            result_vol = 0
            result_vol = result_vol | response_vol[3] << 8
            result_vol = result_vol | response_vol[4]
            result_vol /= 10
            # Write the state of charge to the file
            print("Voltage : ", "{:.2f}".format(result_vol))
            file.write("Voltage: " + str(result_vol) + ';')
            message_vol = can.Message(arbitration_id=0x300, data=result_vol, is_extended_id=True)
            bus.send(message_vol)
        time.sleep(1)

        # Request and receive the temperature data
        ser.write(temp)
        time.sleep(1)
        bytesToRead_temp = ser.inWaiting()
        response_temp = ser.read(bytesToRead_temp)
        response_temp_decoded = libscrc.modbus(response_temp)
        if len(response_temp) >= 6:
            result_temp = 0
            result_temp = result_temp | response_temp[3] << 8
            result_temp = result_temp | response_temp[4]
            result_temp /= 1000
            print("Temperature : ", result_temp)
            file.write("Voltage: " + str(result_temp) + ';')
            message_temp = can.Message(arbitration_id=0x301, data=result_temp, is_extended_id=True)
            bus.send(message_temp)
        time.sleep(1)

        # Cell1     Cell2       Cell3       Cell4       Cell5       Cell6
        # 3 4       7 8         11 12       15 16       19 20       23 24       Module1Temp: 27 28
        # 43 44     47 48       51 52       55 56       59 60       63 64       Module2Temp: 67 68
        # 83 84     87 88       91 92       95 96       99 100      103 104     Module3Temp: 107 108
        # 123 124   127 128     131 132     135 136     139 140     143 144     Module4temp: 147 148
        cellVoltageSum = 0
        # Request and receive the cell voltages
        ser.write(cells)
        time.sleep(1)
        bytesToRead_cell = ser.inWaiting()
        response_vol_cell = ser.read(bytesToRead_cell)
        print(response_vol_cell)
        response_vol_cell_decoded = libscrc.modbus(response_vol_cell)
        i = 3
        moduleTemp = [] * 4
        while i < 148:
            if len(response_vol_cell) >= 16:
                result_vol_cell = 0
                result_vol_cell = result_vol_cell | response_vol_cell[i] << 8
                result_vol_cell = result_vol_cell | response_vol_cell[i+1]
                if i == 27:
                    moduleTemp[1] = result_vol_cell/1000
                    i += 16
                elif i == 67:
                    moduleTemp[2] = result_vol_cell/1000
                    i += 16
                elif i == 107:
                    moduleTemp[3] = result_vol_cell/1000
                    i += 16
                elif i == 147:
                    moduleTemp[4] = result_vol_cell/1000
                    i += 16
                else:
                    cellVoltageSum += result_vol_cell / 10
                    print("Cell ", "{:.2f}".format(result_vol_cell / 1000))
                    print("Module Voltage: ", "{:.2f}".format(moduleTemp[1]), "{:.2f}".format(moduleTemp[2]),
                          "{:.2f}".format(moduleTemp[3]), "{:.2f}".format(moduleTemp[4]))
                    i += 4

        # Write the average voltage to the file
        cellVoltageSum = cellVoltageSum/20*24
        cellVoltageSum /= 100
        file.write("Voltage: " + str(cellVoltageSum) + ';')
        print("Voltage from cells: ", "{:.2f}".format(cellVoltageSum))
        message_voltage_sum = can.Message(arbitration_id=0x302, data=round(cellVoltageSum), is_extended_id=True)
        bus.send(message_voltage_sum)
        time.sleep(1)

        # Find and send the SOC
        result_soc = findsoc(cellVoltageSum, 70, 96)  # değerler değiştirilebilir
        print("SOC: %", result_soc)
        file.write("SOC: %" + str(result_soc) + '\n')
        message_soc = can.Message(arbitration_id=0x302, data=result_soc, is_extended_id=True)
        bus.send(message_soc)
