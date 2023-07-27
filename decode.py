import struct
import numpy as np

UNITS_TABLE = ("V", "A", "VV", "AA", "OU", "W", "SQRT_V", "SQRT_A", "INTEGRAL_V", "INTEGRAL_A", "DT_V", "DT_A",
               "DT_DIV", "Hz", "S", "SA", "PTS", "NULL", "DB", "DBV", "DBA", "VPP", "VDC", "DBM")


def magnitude_to_decimal(index: int):
    return 10 ** ((index - 8) * 3)


with open('SDS00003.bin', 'rb') as file:
    ch_on = struct.unpack('<4i', file.read(4 * 4))
    print(f"{ch_on = }")

    ch_volt_div = tuple(map(lambda x: (x[0] * magnitude_to_decimal(x[1]), UNITS_TABLE[x[2]]),
                                struct.iter_unpack('<dII', file.read(16 * 4))))
    print(f"{ch_volt_div = }")

    ch_vert_offset = tuple(map(lambda x: (x[0] * magnitude_to_decimal(x[1]), UNITS_TABLE[x[2]]),
                               struct.iter_unpack('<dII', file.read(16 * 4))))
    print(f"{ch_vert_offset = }")

    digital_on = struct.unpack('<I', file.read(4))[0]
    print(f"{digital_on = }")

    d_on = struct.unpack('<16I', file.read(4 * 16))
    print(f"{d_on = }")

    time_div = struct.unpack('<dII', file.read(16))
    time_div = (time_div[0] * magnitude_to_decimal(time_div[1]), UNITS_TABLE[time_div[2]])
    print(f"{time_div = }")

    time_delay = struct.unpack('<dII', file.read(16))
    time_delay = (time_delay[0] * magnitude_to_decimal(time_delay[1]), UNITS_TABLE[time_delay[2]])
    print(f"{time_delay = }")

    wave_length = struct.unpack('<I', file.read(4))[0]
    print(f"{wave_length = }")

    sample_rate = struct.unpack('<dII', file.read(16))
    try:
        sample_rate = (sample_rate[0] * magnitude_to_decimal(sample_rate[1]), UNITS_TABLE[sample_rate[2]])
    except IndexError:
        sample_rate = (sample_rate[0] * magnitude_to_decimal(sample_rate[1]), f"N/A ({sample_rate[2]})")
    print(f"{sample_rate = }")

    digital_wave_length = struct.unpack('<I', file.read(4))[0]
    print(f"{digital_wave_length = }")

    digital_sample_rate = struct.unpack('<dII', file.read(16))
    try:
        digital_sample_rate = (digital_sample_rate[0] * magnitude_to_decimal(digital_sample_rate[1]), UNITS_TABLE[digital_sample_rate[2]])
    except IndexError:
        digital_sample_rate = (digital_sample_rate[0] * magnitude_to_decimal(digital_sample_rate[1]), f"N/A ({digital_sample_rate[2]})")
    print(f"{digital_sample_rate = }")

    ch_attenuation = struct.unpack('<4d', file.read(8 * 4))
    print(f"{ch_attenuation = }")

    file.seek(0x800, 0)
    for i, on in enumerate(ch_on):
        if on:
            ch_data = np.frombuffer(struct.unpack(f'<{int(wave_length)}s', file.read(int(wave_length)))[0], dtype=np.uint8)
            ch_data = ((ch_data - 128) * ch_volt_div[0][0] / 25 - ch_vert_offset[0][0]) * ch_attenuation[i]
            print(f"ch{i + 1} data:", ch_data)

    if digital_on:
        for i, on in enumerate(d_on):
            if on:
                digital_data = np.frombuffer(struct.unpack(f'<{int(digital_wave_length)}s', file.read(int(digital_wave_length)))[0], dtype=np.uint8)
                print(f"ch{i + 1} data:", digital_data)
