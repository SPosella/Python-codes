#!python3
import socket
import time
import matplotlib.pyplot as plt
import numpy as np
import communication

# use ggplot style for more sophisticated visuals
plt.style.use('ggplot')

# NUMBER OF POINT TO DRAW FOR EACH TRACK
arraysize = 25
track_color = ['b', 'g', 'r', 'c', 'm', 'y', 'k']


class Track:
    def __init__(self):
        self.values = np.asarray(([0 for i in range(arraysize)]))
        # define other parameters of tracks...
        self.color = 'g'
        self.offset = 1

    def update(self, val):
        self.values = np.append(self.values, val - self.offset)

    def values(self):
        return self.values

    def set_color(self, c):
        self.color = c

    def get_color(self):
        return self.color

    def set_offset(self, off):
        self.offset = off

    def get_offset(self):
        return self.offset


# DEFINE IF WE WANT TRACKS ON SAME PLOT OR IN DIFFERENT SUBPLOT.
# values accepted: 1, 0 or anything else
# I suggest to use multiplot = 1 only if you want to plot few channel because matplotlib draw is poor and slow
MULTIPLOT = 0

OFFSET_BETWEEN_CHANNELS = 25


class SoundTrack:
    def __init__(self, nChannel):
        print("soundtrack initialization with nChannel ", nChannel)
        self.nch = nChannel
        self.tracks = []
        for i in range(nChannel):
            t = Track()
            t.set_color(track_color[i % len(track_color)])
            self.tracks.append(t)

        self.fig = plt.figure(figsize=(13, 6))
        self.lines = []
        if MULTIPLOT == 1:
            self.lines, self.axs = init_multiplot(self.lines, nChannel, self.tracks)
        else:
            self.lines, self.axs = init_multilines(self.lines, nChannel, self.tracks)
            for i in range(len(self.tracks)):
                self.tracks[i].set_offset(OFFSET_BETWEEN_CHANNELS * i)
                print("offset", self.tracks[i].offset)

    def update_track(self, values, i):
        self.tracks[i].update(values)
        self.lines[i].set_ydata(self.tracks[i].values[-arraysize:])
        if MULTIPLOT == 1:
            if np.min(values) <= self.lines[i].axes.get_ylim()[0] or np.max(values) >= self.lines[i].axes.get_ylim()[1]:
                self.lines[i].axes.set_ylim([np.min(self.tracks[i].values) - np.std(self.tracks[i].values),
                          np.max(self.tracks[i].values) + np.std(self.tracks[i].values)])
        #    if np.min(values) <= self.lines[i].axes.get_ylim()[0] or np.max(values) >= self.lines[i].axes.get_ylim()[1]:
        #        self.lines[i].axes.set_ylim([np.min(values) - np.std(values), np.max(values) + np.std(values)])
        #        print("update ax -  min {0} max {1}".format(np.min(values), np.max(values)))

    def update(self, values):
        for i in range(self.nch):
            self.update_track(values[i], i)

        #if np.min(values) <= self.axs.get_ylim()[0] or np.max(values) >= self.axs.get_ylim()[1]:
        #    self.axs.set_ylim([np.min(values) - np.std(values), np.max(values) + np.std(values)])
        #    print("update ax -  min {0} max {1}".format(np.min(values), np.max(values)))
        plt.pause(0.001)

    def get_tracks(self):
        return self.tracks


def live_plotter(x_vec, y1_data, line, identifier='', pause_time=0.001):
    if line == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        fig = plt.figure(figsize=(13, 6))
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line, = ax.plot(x_vec, y1_data, '-o', alpha=0.8)
        # update plot label/title
        plt.ylabel('Y Label')
        plt.title('Title: {}'.format(identifier))
        plt.show()

    # after the figure, axis, and line are created, we only need to update the y-data
    print("y1 data len", len(y1_data))
    line.set_ydata(y1_data)
    # PRINT FPS value
    new_time = time.time()
    print("{0:.2f} fps".format(1. / (new_time - last_time[0])))
    last_time.update({0: new_time})
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data) <= line.axes.get_ylim()[0] or np.max(y1_data) >= line.axes.get_ylim()[1]:
        plt.ylim([np.min(y1_data) - np.std(y1_data), np.max(y1_data) + np.std(y1_data)])
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_time)

    # return line so we can update it again in the next iteration
    return line


def multi_live_plotter(x_vec, y1_data, lines, pause_time=0.001):
    # after the figure, axis, and line are created, we only need to update the y-data
    i = 0
    for line in lines:
        line.set_ydata(y1_data[i])
        # adjust limits if new data goes beyond bounds
        if np.min(y1_data) <= line.axes.get_ylim()[0] or np.max(y1_data) >= line.axes.get_ylim()[1]:
            plt.ylim([np.min(y1_data) - np.std(y1_data), np.max(y1_data) + np.std(y1_data)])
        # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
        plt.pause(pause_time)
        i += 1
    new_time = time.time()
    print("{0:.2f} fps".format(1. / (new_time - last_time[0])))
    last_time.update({0: new_time})
    # return line so we can update it again in the next iteration
    return lines


# this function defines lines on different subplot
def init_multiplot(lines, nChannel, tracks):
    if lines == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        lines = [[] for i in range(nChannel)]

        # INITIALIZE lines
        fig, axs = plt.subplots(nChannel, 1)
        fig.subplots_adjust(hspace=.5, wspace=.001)

        i = 0

        for ax in axs:
            # this is the call to matplotlib that allows dynamic plotting
            # create a variable for the line so we can later update it
            line, = ax.plot(np.linspace(0, 1, arraysize + 1)[0:-1], np.random.randn(arraysize),
                            '-o' + tracks[i].get_color(),
                            color=tracks[i].get_color(), alpha=0.8)

            lines[i] = line
            i += 1
            # update plot label/
            ax.set_ylabel(i)
            # plt.ylabel('Y Label')
    return lines, axs


# this function define lines in same plot
def init_multilines(lines, nChannel, tracks):
    if lines == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        lines = [[] for i in range(nChannel)]

        # INITIALIZE lines
        fig, axs = plt.subplots()
        fig.subplots_adjust(hspace=.5, wspace=.001)
        axs.set_ylim(-2000, 200)
        i = 0

        # this is the call to matplotlib that allows dynamic plotting
        # create a variable for the line so we can later update it
        for i in range(nChannel):
            line, = axs.plot(np.linspace(0, 1, arraysize + 1)[0:-1], np.random.randn(arraysize),
                             '-o' + tracks[i].get_color(),
                             color=tracks[i].get_color(), alpha=0.8)

            lines[i] = line
            i += 1

    return lines, axs


ip_address = '0.0.0.0'
port = 45454

# Create a socket which is used to connect to Sessantaquattro
sq_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sq_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sq_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

# Create start command and get basic setup information
(start_command,
 number_of_channels,
 sample_frequency,
 bytes_in_sample) = communication.create_bin_command(start=1)

sample_from_channels = [0 for i in range(number_of_channels - 4)]

print('Starting to log data: {0} channels with {1} sampling rate'.format(number_of_channels, sample_frequency))
print("number of channels " + str(number_of_channels))
# Open connection to Sessantaquattro
connection = communication.connect_to_sq(sq_socket, ip_address, port, start_command)

last_time = {0: time.time()}

lines = []
line = []

s = SoundTrack(number_of_channels - 4)
i = 0

while True:
    sample_from_channels_as_bytes = communication.read_raw_bytes(
        connection,
        number_of_channels,
        bytes_in_sample)

    # Convert the bytes into integer values
    sample_from_channels = communication.bytes_to_integers(
        sample_from_channels_as_bytes,
        number_of_channels,
        bytes_in_sample,
        output_milli_volts=False)
    # print(sample_from_channels)
    i += 1

    if i % (sample_frequency / 10) == 0:
        new_time = time.time()
        s.update(sample_from_channels)
        print("{0:.2f} fps".format(1. / (new_time - last_time[0])))
        last_time.update({0: new_time})
        i = 0

tracks = s.get_tracks()
