import argparse
import os
import struct
from zipfile import ZipFile
import logging as log

import numpy as np

UNITS_TABLE = ("V", "A", "VV", "AA", "OU", "W", "SQRT_V", "SQRT_A", "INTEGRAL_V", "INTEGRAL_A", "DT_V", "DT_A",
               "DT_DIV", "Hz", "S", "SA", "PTS", "NULL", "DB", "DBV", "DBA", "VPP", "VDC", "DBM")


def magnitude_to_decimal(index: int):
    return 10 ** ((index - 8) * 3)


def decode(filename="SDS00001.bin"):
    with open(f"{filename}", 'rb') as file:
        ch_on = struct.unpack('<4i', file.read(4 * 4))
        log.info(f"{ch_on = }")

        ch_volt_div = tuple(map(lambda x: (x[0] * magnitude_to_decimal(x[1]), UNITS_TABLE[x[2]]),
                                struct.iter_unpack('<dII', file.read(16 * 4))))
        log.info(f"{ch_volt_div = }")

        ch_vert_offset = tuple(map(lambda x: (x[0] * magnitude_to_decimal(x[1]), UNITS_TABLE[x[2]]),
                                   struct.iter_unpack('<dII', file.read(16 * 4))))
        log.info(f"{ch_vert_offset = }")

        digital_on = struct.unpack('<I', file.read(4))[0]
        log.info(f"{digital_on = }")

        d_on = struct.unpack('<16I', file.read(4 * 16))
        log.info(f"{d_on = }")

        time_div = struct.unpack('<dII', file.read(16))
        time_div = (time_div[0] * magnitude_to_decimal(time_div[1]), UNITS_TABLE[time_div[2]])
        log.info(f"{time_div = }")

        time_delay = struct.unpack('<dII', file.read(16))
        time_delay = (time_delay[0] * magnitude_to_decimal(time_delay[1]), UNITS_TABLE[time_delay[2]])
        log.info(f"{time_delay = }")

        wave_length = struct.unpack('<I', file.read(4))[0]
        log.info(f"{wave_length = }")

        sample_rate = struct.unpack('<dII', file.read(16))
        try:
            sample_rate = (sample_rate[0] * magnitude_to_decimal(sample_rate[1]), UNITS_TABLE[sample_rate[2]])
        except IndexError:
            sample_rate = (sample_rate[0] * magnitude_to_decimal(sample_rate[1]), f"N/A ({sample_rate[2]})")
        log.info(f"{sample_rate = }")

        digital_wave_length = struct.unpack('<I', file.read(4))[0]
        log.info(f"{digital_wave_length = }")

        digital_sample_rate = struct.unpack('<dII', file.read(16))
        try:
            digital_sample_rate = (
            digital_sample_rate[0] * magnitude_to_decimal(digital_sample_rate[1]), UNITS_TABLE[digital_sample_rate[2]])
        except IndexError:
            digital_sample_rate = (
            digital_sample_rate[0] * magnitude_to_decimal(digital_sample_rate[1]), f"N/A ({digital_sample_rate[2]})")
        log.info(f"{digital_sample_rate = }")

        ch_attenuation = struct.unpack('<4d', file.read(8 * 4))
        log.info(f"{ch_attenuation = }")

        time = (time_delay[0] - (time_div[0] * 7), 1 / sample_rate[0])
        time = (time[0], time[1], sample_rate[0], np.arange(time[0], time[0] + wave_length * time[1], time[1]))
        log.info(f"{time = }")
        analog_data = []
        digital_data = []
        file.seek(0x800, 0)
        for i, on in enumerate(ch_on):
            if on:
                ch_data = np.frombuffer(struct.unpack(f'<{int(wave_length)}s', file.read(int(wave_length)))[0],
                                        dtype=np.uint8).astype(np.int16)

                ch_data = ((ch_data - 128) * ch_volt_div[0][0] / 25 - ch_vert_offset[0][0]) * ch_attenuation[i]
                ch_data = ch_data.astype(np.dtype(np.float32).newbyteorder("<"))
                log.info(f"ch{i + 1} data: {ch_data}")
                analog_data.append(ch_data)
            else:
                analog_data.append(None)

        if digital_on:
            for i, on in enumerate(d_on):
                if on:
                    ch_data = np.frombuffer(
                        struct.unpack(f'<{int(digital_wave_length)}s', file.read(int(digital_wave_length)))[0],
                        dtype=np.uint8)
                    log.info(f"ch{i + 1} data: {ch_data}")
                    digital_data.append(ch_data)
                else:
                    digital_data.append(None)
    return analog_data, digital_data, time


def save_analog_to_file(data: bytes | np.ndarray, filename: str = 'ch1.bin'):
    """
    :param data: data of analog channel to save
    :param filename: filename to save as
    :type data: bytes like object, with float32 little endian encoding. ex: ndarray with dtype float32
    :type filename: str
    """
    with open(f"{filename}", 'wb') as analog_file:
        analog_file.write(data)


def save_digital_to_file(data: bytes | np.ndarray, filename: str = 'd1.bin'):
    raise NotImplementedError()


def save_to_sigrok_zip(analog_data: list[bytes | np.ndarray], digital_data: list[bytes | np.ndarray],
                       sample_rate: int | float, filename: str = "decode.sr") -> None:
    with ZipFile(filename, "w") as zipfile:
        zipfile.writestr("version", "2")
        zipfile.writestr("metadata",  f"""[device 1]
total analog={len(analog_data)}
total probes={len(digital_data)}
samplerate={int(sample_rate)}
""" +
                         "\n".join(f"analog{i+1}=Ch{i + 1}" for i, v in enumerate(analog_data) if v is not None) +
                         "\n".join(f"probe{i+1}=D{i + 1}" for i, v in enumerate(digital_data) if v is not None))
        for i, data in enumerate(analog_data):
            if data is not None:
                zipfile.writestr(f"analog-1-{i+1}-1", data)
        # TODO: write digital data to sr file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="binary file to decode")
    parser.add_argument("-r", "--raw", help="write to raw binary file instead of sigrok zip file", action='store_true')
    parser.add_argument("-v", "--verbose", help="print verbose logs", action='store_true')
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    analog_data, digital_data, time = decode(args.filename)
    if args.raw:
        for i, data in enumerate(analog_data):
            if data is not None:
                save_analog_to_file(data, f"{os.path.splitext(args.filename)[0]}-ch{i+1}.bin")
        # TODO: write digital data
        print("Raw file saved!")
    else:
        filename = f"{os.path.splitext(args.filename)[0]}.sr"
        save_to_sigrok_zip(analog_data, digital_data, time[2], filename)
        print(f"Sigrok file saved as {filename}")


if __name__ == "__main__":
    main()
