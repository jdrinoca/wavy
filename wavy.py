
# PyAudio requires PortAudio
import pyaudio
import numpy as np
from scipy import signal as sig
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation


freq = []
PSD = []

# callback loop for audio processing
def callback(in_data, frame_count, time_info, status):
    global freq, PSD

    # convert audio stream to correct format
    audio = np.frombuffer(in_data, dtype=np.int16)

    # fft - generate frequency and power spectrum arrays
    freq, PSD = sig.periodogram(audio, sampleRate, nfft=sampleRate/10)

    # return, continue audio processing
    return (in_data, pyaudio.paContinue)

# hide matplotlib toolbar
matplotlib.rcParams['toolbar'] = 'None'

# create a fullscreen black window
fig = plt.figure()
mng = plt.get_current_fig_manager()
mng.window.state('zoomed')
fig.patch.set_facecolor('black')

# number of frequency divisions
numDivs = 80

# generate plot limits and hide axes
ax = fig.add_axes([0, 0, 1, 1], frameon=False)
ax.set_xlim(0,1.1), ax.set_xticks([])
ax.set_ylim(-40, 40), ax.set_yticks([])
fig.canvas.set_window_title('wavy')


# audio sampling parameters
chunk = 256
bandwidth = 2
channels = 1
sampleRate = 44100

# create PyAudio instance
p = pyaudio.PyAudio()

# get connected audio device names
deviceInfo = p.get_host_api_info_by_index(0)
numDevices = deviceInfo.get('deviceCount')
inputChannel = 0

# look for audio mirror named 'Stereo Mix' and save that channel
# Stereo Mix has to be enabled for this to work
for i in range(0,numDevices):
    if 'Stereo Mix' in p.get_device_info_by_host_api_device_index(0, i).get('name'):
        inputChannel = i

# start audio sampling
try:
    stream = p.open(format=p.get_format_from_width(bandwidth),
                    channels=channels,rate=sampleRate,
                    input=True,
                    output=False,
                    input_device_index=inputChannel,
                    frames_per_buffer=chunk,
                    stream_callback=callback)
# quit if Stereo Mix is not available
except:
    print('Error - Enable Stereo Mix')
    quit()

divs = np.zeros(numDivs)

# linear colormap normalized to numDivs
cMap = matplotlib.pyplot.get_cmap('gist_rainbow')
cInd = matplotlib.colors.Normalize(vmin=0, vmax=numDivs)

# create frequency plot using matplotlib lines
waves = []
for i in range(0, numDivs):
    wave, = plt.plot([0.05 + i/numDivs, 0.05 + i/numDivs], [0,0], color=cMap(cInd(i)), linewidth = 3)
    waves.append(wave)

# generate frequency spectrum
freqDivs = []
freqDivs.append([0])
freqDivs.append([1,2])
for i in range(2, numDivs):
    prevLow = freqDivs[i-1][0]
    prevHigh = freqDivs[i-1][1]

    freqDivs.append([prevHigh+1,prevHigh+1+(prevHigh-prevLow)*1.0625])

    # use the full fft spectrum
    if len(freqDivs) == numDivs:
        freqDivs[numDivs-1] = [freqDivs[numDivs-1][0], len(freq)]


amp = np.zeros(numDivs)

# animation loop
def update(frame):
    global freq, PSD

    # take PSD data and create amplitude values for the frequency plot
    divs[0] = PSD[0]**0.5
    waves[0].set_ydata([-divs[0],divs[0]])
    for i in range(1, numDivs):
        
        # square-root of the average 'volume' for each frequency range
        divs[i] = np.average(PSD[int(freqDivs[i][0]):int(freqDivs[i][1])])**0.5

        # instant growth, proportional decay
        if divs[i] > amp[i]: amp[i] = divs[i]
        elif divs[i] < amp[i]: amp[i] = amp[i]-(amp[i]-divs[i])/2

        waves[i].set_ydata([-amp[i],amp[i]])
        

# start audio stream and animations
stream.start_stream()
animation = FuncAnimation(fig, update, interval=15)
plt.show()

# stop audio stream when the plot is closed
stream.stop_stream()
stream.close()
p.terminate()