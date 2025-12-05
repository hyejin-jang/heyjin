import struct
import sys
import json
import os

def parse_smart_bin(filepath):
    """Parse NVMe SMART binary log to dict"""
    with open(filepath, 'rb') as f:
        data = f.read(512)
    
    if len(data) < 512:
        raise ValueError("Invalid SMART log size")
    
    result = {}
    
    # Critical Warning
    result['critical_warning'] = data[0]
    
    # Temperature (Kelvin -> Celsius)
    temp_kelvin = struct.unpack('<H', data[1:3])[0]
    result['temperature_celsius'] = temp_kelvin - 273 if temp_kelvin > 0 else 0
    
    # Spare
    result['available_spare_pct'] = data[3]
    result['spare_threshold_pct'] = data[4]
    result['percentage_used'] = data[5]
    
    # Data Units (16 bytes = 128 bits, use first 8 bytes for simplicity in this mock)
    # In real world, handle full 128-bit integers
    result['data_units_read'] = struct.unpack('<Q', data[32:40])[0]
    result['data_units_written'] = struct.unpack('<Q', data[48:56])[0]
    result['host_read_commands'] = struct.unpack('<Q', data[64:72])[0]
    result['host_write_commands'] = struct.unpack('<Q', data[80:88])[0]
    
    # Power
    result['power_on_hours'] = struct.unpack('<Q', data[128:136])[0]
    result['power_cycles'] = struct.unpack('<Q', data[144:152])[0]
    
    # Temperature Sensors
    result['temperature_sensors'] = []
    for i in range(8):
        offset = 200 + i * 2
        sensor_kelvin = struct.unpack('<H', data[offset:offset+2])[0]
        if sensor_kelvin > 0:
            result['temperature_sensors'].append(sensor_kelvin - 273)
        else:
            result['temperature_sensors'].append(None)
    
    # Calculations
    # WAF = NAND Writes / Host Writes (Approximation using Data Units Written as NAND Writes proxy if internal metrics unavailable, 
    # but strictly speaking Data Units Written in SMART is Host Data. 
    # For this mock, we'll assume Data Units Written is Host Data and we don't have NAND writes in standard SMART.
    # Wait, standard SMART doesn't have NAND writes. 
    # So WAF cannot be calculated purely from standard SMART without vendor specific logs.
    # However, for the sake of the "Mock-up" requested by user which included WAF, 
    # let's simulate WAF or just leave it as placeholder/derived if we had NAND info.
    # Let's add a note or simulate it if we were parsing a vendor log. 
    # For now, let's just calculate Host Write Average Size or something else, OR
    # just output what we have.
    
    result['total_gb_read'] = (result['data_units_read'] * 512 * 1000) / (1024**3) # Data Units is 1000 units of 512 bytes
    result['total_gb_written'] = (result['data_units_written'] * 512 * 1000) / (1024**3)
    
    return result

def save_to_json(data, output_path):
    """Save parsed data to JSON"""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    if len(sys.argv) < 3:
        print("Usage: python nvme_smart_parser.py <input.bin> <output.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        data = parse_smart_bin(input_file)
        save_to_json(data, output_file)
        print(f"✅ Parsed {input_file} -> {output_file}")
        print(f"Temperature: {data['temperature_celsius']}°C")
        print(f"Spare: {data['available_spare_pct']}%")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
