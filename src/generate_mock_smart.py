import struct
import random
import sys

def generate_mock_smart(output_file):
    # Create 512 bytes buffer initialized to 0
    data = bytearray(512)
    
    # Critical Warning (0 = OK)
    data[0] = 0
    
    # Temperature (Kelvin)
    # 35 Celsius = 308 Kelvin
    temp_c = random.randint(30, 75)
    temp_k = temp_c + 273
    struct.pack_into('<H', data, 1, temp_k)
    
    # Available Spare
    data[3] = random.randint(10, 100)
    
    # Spare Threshold
    data[4] = 10
    
    # Percentage Used
    data[5] = random.randint(0, 95)
    
    # Data Units Read (1000 units of 512 bytes)
    units_read = random.randint(100000, 10000000)
    struct.pack_into('<Q', data, 32, units_read)
    
    # Data Units Written
    units_written = random.randint(100000, 10000000)
    struct.pack_into('<Q', data, 48, units_written)
    
    # Host Read Commands
    host_read = random.randint(1000000, 100000000)
    struct.pack_into('<Q', data, 64, host_read)
    
    # Host Write Commands
    host_write = random.randint(1000000, 100000000)
    struct.pack_into('<Q', data, 80, host_write)
    
    # Power On Hours
    poh = random.randint(100, 50000)
    struct.pack_into('<Q', data, 128, poh)
    
    # Power Cycles
    cycles = random.randint(10, 5000)
    struct.pack_into('<Q', data, 144, cycles)
    
    # Temperature Sensors (Mocking 3 sensors)
    for i in range(3):
        offset = 200 + i * 2
        s_temp = temp_k + random.randint(-5, 5)
        struct.pack_into('<H', data, offset, s_temp)
        
    with open(output_file, 'wb') as f:
        f.write(data)
    
    print(f"Generated mock SMART log: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_mock_smart.py <output.bin>")
    else:
        generate_mock_smart(sys.argv[1])
