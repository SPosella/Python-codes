#!python3
# -------------------------------------------------------
# Module to connect to Sessantaquattro Bio signal data logger
#
import datetime
import multiprocessing
import socket  # we will need this for establishing the communication with Sessantaquattro
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

CONVERSION_FACTOR = 0.000286  # conversion factor needed to get values in mV


# Convert integer to bytes
def integer_to_bytes(command):
    return int(command).to_bytes(2, byteorder="big")


# Convert byte-array value to an integer value and apply two's complement
def convert_bytes_to_int(bytes_value, bytes_in_sample):
    value = None
    if bytes_in_sample == 2:
        # Combine 2 bytes to a 16 bit integer value
        value = \
            bytes_value[0] * 256 + \
            bytes_value[1]
        # See if the value is negative and make the two's complement
        if value >= 32768:
            value -= 65536
    elif bytes_in_sample == 3:
        # Combine 3 bytes to a 24 bit integer value
        value = \
            bytes_value[0] * 65536 + \
            bytes_value[1] * 256 + \
            bytes_value[2]
        # See if the value is negative and make the two's complement
        if value >= 8388608:
            value -= 16777216
    else:
        raise Exception(
            "Unknown bytes_in_sample value. Got: {}, "
            "but expecting 2 or 3".format(bytes_in_sample))
    return value


# Create the binary command which is sent to Sessantaquattro
# to start or stop the communication with wanted data logging setup
def create_bin_command(start=1):
    rec = 0
    trig = 0
    ext = 0
    hpf = 1
    hres = 1
    mode = 0
    nch = 0
    fsamp = 0
    getset = 0

    command = 0
    command = command + start
    command = command + rec * 2
    command = command + trig * 4
    command = command + ext * 16
    command = command + hpf * 64
    command = command + hres * 128
    command = command + mode * 256
    command = command + nch * 2048
    command = command + fsamp * 8192
    command = command + getset * 32768

    number_of_channels = None
    sample_frequency = None
    bytes_in_sample = None

    if nch == 0:
        if mode == 1:
            number_of_channels = 8
        else:
            number_of_channels = 12
    elif nch == 1:
        if mode == 1:
            number_of_channels = 12
        else:
            number_of_channels = 20
    elif nch == 2:
        if mode == 1:
            number_of_channels = 20
        else:
            number_of_channels = 36
    elif nch == 3:
        if mode == 1:
            number_of_channels = 36
        else:
            number_of_channels = 68
    else:
        raise Exception('Wrong value for nch. Got: {0}', nch)

    if fsamp == 0:
        if mode == 3:
            sample_frequency = 2000
        else:
            sample_frequency = 500
    elif fsamp == 1:
        if mode == 3:
            sample_frequency = 4000
        else:
            sample_frequency = 1000
    elif fsamp == 2:
        if mode == 3:
            sample_frequency = 8000
        else:
            sample_frequency = 2000
    elif fsamp == 3:
        if mode == 3:
            sample_frequency = 16000
        else:
            sample_frequency = 4000
    else:
        raise Exception('wrong value for fsamp. Got: {fsamp}', fsamp)

    if hres == 1:
        bytes_in_sample = 3
    else:
        bytes_in_sample = 2

    if (
            not number_of_channels or
            not sample_frequency or
            not bytes_in_sample):
        raise Exception(
            "Could not set number_of_channels "
            "and/or and/or bytes_in_sample")

    return (integer_to_bytes(command),
            number_of_channels,
            sample_frequency,
            bytes_in_sample)


# Convert channels from bytes to integers
def bytes_to_integers(
        sample_from_channels_as_bytes,
        number_of_channels,
        bytes_in_sample,
        output_milli_volts):
    channel_values = []
    # Separate channels from byte-string. One channel has
    # "bytes_in_sample" many bytes in it.
    for channel_index in range(number_of_channels):
        channel_start = channel_index * bytes_in_sample
        channel_end = (channel_index + 1) * bytes_in_sample
        channel = sample_from_channels_as_bytes[channel_start:channel_end]

        # Convert channel's byte value to integer
        value = convert_bytes_to_int(channel, bytes_in_sample)

        # Convert bio measurement channels to milli volts if needed
        # The 4 last channels (Auxiliary and Accessory-channels)
        # are not to be converted to milli volts
        if output_milli_volts and channel_index < (number_of_channels - 4):
            value *= CONVERSION_FACTOR
        channel_values.append(value)
    return channel_values


#     Read raw byte stream from data logger. Read one sample from each
#     channel. Each channel has 'bytes_in_sample' many bytes in it.
def read_raw_bytes(connection, number_of_all_channels, bytes_in_sample):
    buffer_size = number_of_all_channels * bytes_in_sample
    new_bytes = connection.recv(buffer_size)
    return new_bytes


# Connect to Sessantaquattro's TCP socket and send start command
def connect_to_sq(
        sq_socket,
        ip_address,
        port,
        start_command):
    sq_socket.bind((ip_address, port))
    sq_socket.listen(1)
    print('waiting for connection...')
    conn, addr = sq_socket.accept()
    print('Connection from address: {0}'.format((addr)))
    conn.send(start_command)
    return conn


# Disconnect from Sessantaquattro by sending a stop command
def disconnect_from_sq(conn):
    if conn is not None:
        (stop_command,
         _,
         __,
         ___) = create_bin_command(start=0)
        conn.send(stop_command)
        conn.shutdown(2)
        conn.close()
    else:
        raise Exception(
            "Can't disconnect because the"
            "connection is not established")

