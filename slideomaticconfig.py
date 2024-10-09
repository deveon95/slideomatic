## Configuration variables
# Number of different local music playlists
localmusicnumber = 2
# Specified attribute to use for searching for each local music programme
localmusicsearchfield = ["Artist", "Album"]
# Value of specified attribute used to identify local music for inclusion
localmusicsearchdata = ["Ceefax", "Mix"]
# Path and file match criteria for slideshow images
slideshowpath = "/home/pi/slideshow/*.jpg"
# Commands for formatting the status output for the caption
localmusicstatuscommand = ['mpc', '-f', '%album%: %title%', 'current']
internetradiostatuscommand = ['mpc', 'current']
localmusicline1 = ['mpc', '-f', '%album%']
localmusicline2 = ['mpc', '-f', '%title%']
internetradioline1 = ['mpc', '-f', '%name%']
internetradioline2 = ['mpc', '-f', '%title%']
# Offsets for correcting image position so that it appears in the centre
vbioffset = 24
horoffset = 9
# Background colours
defaultbg = (0,0,0)
defaultbgcaption = defaultbg
textfg = (191,191,191)
# display current programme number on screen
enableprogrammenumber = True
# Margin around caption (left and right) for overscan
captionmargin = 40
# Font height in pixels
fontsize = 40
# Caption height in pixels
captionheight = (fontsize * 2)
# GPIO pins for the programme selection switch (N.B. Pin 27 on later Pis is pin 21 on original Pi)
switchAGPIO = 12
switchBGPIO = 16
switchCGPIO = 20
switchDGPIO = 21
# Audio enable GPIO for switching the audio mux between master audio and this Pi
audioEnGPIO = 26
useAudioEn = False
# Serial port
serialPort = '/dev/ttyS0'
# Fixed deduction due to font.size returning value with blank line of pixels added
fontHeightDeduct = 1
# Path to font file
fontpath = "/usr/share/fonts/teletext4.ttf"
# Timebase in seconds for all operations including sampling the programme switch
timebase = 0.1
# Interval for running mpc command to get caption (in units of timebase)
captioninterval = (2 * 10)
# Interval for changing the slideshow image (in units of timebase)
imageinterval = ((60 * 10) * 10)
# Set switchinvert to True if switch contacts are closed when set to 0 (disconnected switch will also be read as 15),
# or False if switch contacts are open when set to 0 (disconnected switch will also be read as 0)
switchinvert = False
# number of consistent samples of the switch required to change the programme;
# this prevents unnecessary server requests being made when moving the switch multple positions
# and protects against the spurious outputs that BCD-coded thumbwheel switches generate when incrementing
switchsamplecount = 10
