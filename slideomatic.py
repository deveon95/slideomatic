# slideomatic.py
# Displays slideshow of images along with caption of currently playing info from mpc.
# Requires mpc and mpd to be installed.
#
# Internet radio stations must be added using mpc.
# Stations can be added while tvscreen.py is running.
# Once satisfied with the stations, use $ mpc save internetradio to save them.
#
# This script will then play local music when the rotary switch is set to < localmusicnumber
# or play an internet radio station when the switch is in any other position.
#
# Local music is to be stored in the mpd music folder configured in /etc/mpd.conf
# - default is /var/lib/mpd/music (files can be in subfolders) -
# and music corresponding to each switch position is added to the playlist according
# to the criteria set in the localmusicsearchfield and localmusicsearchdata arrays.
#
# Local music is only rescanned at the start of playback
# so a different programme needs to be selected then the original re-selected for
# any newly added files to be included.

## Configuration variables
# Moved to slideomaticconfig.py

import os,sys,pygame,subprocess,glob,random,time,signal,gpiozero,array,serial
from unicodedata import normalize
from slideomaticconfig import *

# Sigterm handler
# To resolve problem of hanging at display.set_mode until Ctrl+C is pressed on subsequent runs
# https://stackoverflow.com/a/21817746
def signal_handler(signal, frame):
	time.sleep(0.1)
	print("Quitting")
	pygame.display.quit()
	pygame.quit()
	print("pygame finished")
	time.sleep(0.1)
	quit()

# draw some text into an area of a surface (copied from Pygame wiki)
# automatically wraps words
# returns any text that didn't get blitted
def drawText(surface, text, color, rect, font, aa=False, bkg=None):
    rect = pygame.Rect(rect)
    y = rect.top
    lineSpacing = -2

    # get the height of the font
    fontHeight = font.size("TgQ")[1] - fontHeightDeduct

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word
        if i < len(text): 
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text

def getSwitchPos(switchAValue, switchBValue, switchCValue, switchDValue):
	if switchinvert == False:
		# Switch contacts are all open when switch position is 0
		return ((switchAValue * 8 + switchBValue * 4 + switchCValue * 2 + switchDValue))
	else:
		# Switch contacts are all closed when switch position is 0
		return (15 - (switchAValue * 8 + switchBValue * 4 + switchCValue * 2 + switchDValue))

subprocess.run(['mpc', 'rescan'], check = True)

# set up display driver
print("Configuring display")
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.init()
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
pygame.mouse.set_visible(0)

# set up signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# get listing of slideshow images
filenames = glob.glob(slideshowpath)
print("Checked for slideshow images")
if len(filenames) == 0:
	raise Exception("No slideshow images found in specified directory" + slideshowpath)
else:
	print("Slideshow images found: " + str(len(filenames)))

# set up font
font = pygame.font.Font(fontpath, fontsize)

running = True
imageloopcounter = imageinterval
captionloopcounter = captioninterval
# Initialise with nonsense strings
nowplayingold = "swefasdgfrhjy"
nowplaying = "swefasdgfrhjy"

# set up GPIO
switchA = gpiozero.DigitalInputDevice(switchAGPIO,True,None,0.1)
switchB = gpiozero.DigitalInputDevice(switchBGPIO,True,None,0.1)
switchC = gpiozero.DigitalInputDevice(switchCGPIO,True,None,0.1)
switchD = gpiozero.DigitalInputDevice(switchDGPIO,True,None,0.1)
switchPosOld = 0
switchPosNew = getSwitchPos(switchA.value, switchB.value, switchC.value, switchD.value)
switchSamples = array.array('i', [switchPosNew] * switchsamplecount)
firstRun = True
if useAudioEn == True:
	audioEn = gpiozero.LED(audioEnGPIO)

# set up serial port
ser = serial.Serial(
	port = serialPort,
	baudrate = 19200,
	parity = serial.PARITY_NONE,
	stopbits = serial.STOPBITS_ONE,
	bytesize = serial.EIGHTBITS,
	timeout = 1
)
# serial write
ser.write(str.encode("\x08" + str(os.uname()[1]) + "\n"))

while running:
	# short delay
	time.sleep(timebase)

	# Programme switch section
	for i in range(switchsamplecount - 1, 0, -1):
		switchSamples[i] = switchSamples[i - 1]
	# Calculate switch position
	switchSamples[0] = getSwitchPos(switchA.value, switchB.value, switchC.value, switchD.value)
	switchPositionValid = True
	# Check whether switch position is valid - value must be the same for 5 samples in a row
	for i in range(0, switchsamplecount - 1):
		if switchSamples[i] != switchSamples[0]:
			switchPositionValid = False
	if (switchPositionValid == True):
		switchPosNew = switchSamples[0]
	#print(switchSamples)
	# If the switch position has changed
	if (switchPosOld != switchPosNew) or (firstRun == True):
		print("New switch position: " + str(switchPosNew) + " was: " + str(switchPosOld))
		if (switchPosNew == 0 and useAudioEn == True):
			subprocess.run(['mpc', 'stop'])
			# use master audio
			audioEn.off()
		else:
			if (useAudioEn == True):
				# Use audio from this pi
				audioEn.on()
				# Adjust switch position index temporarily because
				# position 0 is now used for the master audio
				switchPosNew -= 1
			#endif
			if (switchPosNew >= localmusicnumber):
				# internet radio mode
				if (switchPosOld < localmusicnumber):
					# Was in local music mode so need to load internet radio playlist
					subprocess.run(['mpc', 'stop'])
					subprocess.run(['mpc', 'clear'])
					subprocess.run(['mpc', 'random', 'off'])
					subprocess.run(['mpc', 'single', 'on'])
					subprocess.run(['mpc', 'load', 'internetradio'])
				#endif
				# play new programme
				subprocess.run(['mpc', 'play', str(switchPosNew + 1 - localmusicnumber)])
			else:
				# local music mode
				subprocess.run(['mpc', 'stop'])
				subprocess.run(['mpc', 'clear'])
				subprocess.run(['mpc', 'findadd', localmusicsearchfield[switchPosNew], localmusicsearchdata[switchPosNew]])
				subprocess.run(['mpc', 'random', 'on'])
				subprocess.run(['mpc', 'single', 'off'])
				subprocess.run(['mpc', 'play'])
			#endif
			if (useAudioEn == True):
				switchPosNew += 1
			#endif
		#endif
		# set captionloopcounter so that caption will be fetched in one second, allowing time to connect
		captionloopcounter = captioninterval - 10
		# invalidate caption with nonsense data
		nowplayingold = "ukiwequkilqwef"
		# reprint the image so that the whole image including caption area is shown
		screen.fill(defaultbg)
		# ... but not yet as image hasn't been defined yet; it will be next time
		if (firstRun == False):
			screen.blit(image,(int(imagexpos),int(imageypos)))
		pygame.display.update()
		switchPosOld = switchPosNew
		firstRun = False
	#endif

	if enableprogrammenumber == True:
		pygame.draw.rect(screen, defaultbgcaption, (captionmargin+horoffset,vbioffset+50,48,fontsize))
		drawText(screen, (' ' if switchPositionValid == True else '#') + str(switchSamples[0]) + ' ', textfg, (captionmargin+horoffset,vbioffset+50,48,fontsize), font)
		pygame.display.update()

	# Image generation secton
	if imageloopcounter < imageinterval:
		imageloopcounter = imageloopcounter + 1
	else:
		imageloopcounter = 0
		# generate a new image index
		currentimagepath = filenames[random.randint(0,len(filenames)-1)]
		image = pygame.image.load(currentimagepath).convert()
		# Display image centred
		imagexpos = (screen.get_width()-image.get_width())/2 + horoffset
		imageypos = (screen.get_height()-image.get_height())/2 + vbioffset
		screen.fill(defaultbg)
		screen.blit(image,(int(imagexpos),int(imageypos)))  
		# write nonsense to nowplayingold to regenerate caption
		nowplayingold = "jfsfkgadljkkl"
		captionloopcounter = captioninterval
	#endif

	# Caption generation section
	if captionloopcounter < captioninterval:
		captionloopcounter = captionloopcounter + 1
	else:
		captionloopcounter = 0

		# determine whether to use status format command for local music or internet radio
		if (switchPosNew < localmusicnumber):
			statuscommand = localmusicstatuscommand
		else:
			statuscommand = internetradiostatuscommand
		# get now playing info using the mpc status command
		# use normalize to convert combining diacritical marks into their simplest form to avoid
		# accented characters returned by some radio stations showing as boxes
		nowplaying = normalize("NFC", subprocess.check_output(statuscommand).decode().split('\n')[0])
		# Check that valid now playing info is available
		# 'http' would suggest that it's just the URL and 'volume:' would suggest that mpc is stopped
		if nowplaying.startswith('http') == False and nowplaying.startswith('volume:') == False and nowplaying != "" and nowplaying.isspace() == False:
			if nowplaying != nowplayingold:
				nowplayingold = nowplaying
				# Draw rectangle to cover up old caption
				pygame.draw.rect(screen, defaultbgcaption, (0, screen.get_height()-captionheight-1, screen.get_width(), screen.get_height()))
				# Render new caption and copy it to screen (with word wrap)
				drawText(screen, nowplaying, textfg, ((captionmargin+horoffset, screen.get_height()-captionheight-1), (screen.get_width()-int(captionmargin*2)-horoffset, captionheight)), font) 
				# update screen
				pygame.display.update()
				if (switchPosNew < localmusicnumber):
					line1 = normalize("NFC", subprocess.check_output(localmusicline1).decode().split('\n')[0])
					line2 = normalize("NFC", subprocess.check_output(localmusicline2).decode().split('\n')[0])
					ser.write(str.encode("\x08" + line1 + "\n" + line2))
				else:
					line1 = normalize("NFC", subprocess.check_output(internetradioline1).decode().split('\n')[0])
					line2 = normalize("NFC", subprocess.check_output(internetradioline2).decode().split('\n')[0])
					ser.write(str.encode("\x08" + line1 + "\n" + line2))
				# nothing for 'else' in this case because old now playing info is still valid
			#endif
		else:
			if nowplaying != nowplayingold:
				#reprint the image so that the whole image including caption area is shown
				screen.fill(defaultbg)
				screen.blit(image,(int(imagexpos),int(imageypos)))
				pygame.display.update()
				# Print hostname on Insertomatic LCD
				ser.write(str.encode("\x08" + str(os.uname()[1]) + "\n"))
				if (useAudioEn == True) and (switchPosNew == 0):
					ser.write(str.encode("Audio routed from P3"))
				# set nowplayingold here, otherwise if the now playing info comes back and is the same
				# as it was before, it won't be displayed.
				nowplayingold = nowplaying
			#endif
		#endif
	#endif

	# press Ctrl+C to trigger quit
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		else:
			print("Event type: " + str(event.type))

# exit
pygame.display.quit()
pygame.quit()
quit()
