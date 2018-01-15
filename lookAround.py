#!/usr/bin/env python2
from psychopy import core, visual, event
import numpy as np

## constants
# An average of n * mean(tVisMin, tVisMax)/(mean(tVisMin, tVisMax)+mean(tInvisMin, tInvisMax)) stimuli 
# is visible at any time. Times are rounded down to whole frames.
nStimuli  = 10          # total number of stimuli, visible + invisible, one is target, others are distractors
tVisMin   = 1.0         # (s) minimum time to stay visible
tVisMax   = 5.0         # (s) maximum time to stay visible
tVisTarget= 0.2         # (s) time that target stays visible
tInvisMin = 1.0         # (s) minimum time to stay invisible
tInvisMax = 5.0         # (s) maximum time to stay invisible
frameRate = 60          # (Hz) make sure this matches the actual framerate
targetProbability = 0.2 # chance that a new stimulus is a target
targetWaitTime = 5.0    # (s) minimum time between onset of two targets
minDistance = 10        # (cm) minimum distance between object origins

## globals (more after window initialization)
# mouse state 0: awaiting click for detection, 1: awaiting release after detection, 
#   2: awaiting click for pointing, 3: awaiting release after pointing
mState = 0
# position of all stimuli, must be kept in sync with stimuli[][].pos
positions = np.full([nStimuli, 2], np.inf)
# visible and invisible time of stimulus in frames
times = np.empty([nStimuli, 2], dtype='int')
shapes = np.empty([nStimuli], dtype='int') 
# when is a new target allowed (frame number)
targetAllowedTime = 0

## function definitions
def pickPosition():
	""" find non overlapping position """
	# distance of closest neighbour
	distance = 0
	while distance < minDistance:
		# pick random position not too close to the edge
		p = np.random.uniform(-0.5, 0.5, [2])*(winSizeCm-minDistance)
		# calculate distances to all others
		distances = np.sqrt(np.sum((positions - p)**2, axis=1))
		# find closest neighbour
		distance = np.min(distances)
	return p

def resetStimulus(i, frame=0, target=False, skipVisible=False):
	""" start a new cycle for a stimulus, starting with some visible time, followed by some invisible time 
	i = stimulus number
	frame = current frame
	skipVisible = skip the visible part of the cycle, start invisible
	"""
	global targetAllowedTime
	# choose shape from distractors if not a target
	if target:
		shapes[i] = targetShape
	else:
		shapes[i] = distractorShapes[np.random.randint(0, nShapes-1)]

	# reset own position
	positions[i,:] = np.inf # necessary to prevent discarding due to self-overlap
	# set position, both for stimulus and posiitons array
	positions[i] = stimulus[shapes[i]].pos = pickPosition()

	# set visible time
	if target:
		times[i, 0] = int(tVisTarget*frameRate) + frame
		targetAllowedTime = times[i, 1] + int(targetWaitTime*frameRate) 
		print("target at frame {:d} at position {:6.1f},{:6.1f}".format(frame, positions[i][0], positions[i][1]))
	else:
		times[i, 0] = int((np.random.random()*(tVisMax - tVisMin)+ tVisMin)*frameRate) + frame
	# set invisible time
	times[i, 1] = int((np.random.random()*(tInvisMax - tInvisMin)+ tInvisMin)*frameRate) + times[i, 0]

	if skipVisible:
		times[i] -= times[i, 0]
	

## script,  initialization
# initialize PsychoPy
win = visual.Window(size=(800, 600), monitor='projector', units='cm', fullscr=False)
mouse = event.Mouse(visible=False)

# check if monitor calibration is present
if not win.scrWidthCM or not win.scrWidthPIX:
	print("Please make a monitor called 'projector' in the monitor center")

# prepare all possible stimuli for speeds optimization
# add more stimuli if you like
stimuli = [ [
	visual.Polygon(win, edges=3, radius=3, fillColor='green'),
	visual.Polygon(win, edges=5, radius=3, fillColor='white'),
	visual.Circle(win, radius=2.5, fillColor='red'),
	visual.Rect(win, width=3, height=6, fillColor='blue'),
	visual.Rect(win, width=4, height=4, fillColor='yellow'),
	] for i in range(nStimuli) ]

# more globals
nShapes = len(stimuli[0]) # number of different shapes
targetShape = np.random.randint(nShapes) # index of target stimulus in stimuli
distractorShapes = np.setdiff1d(np.arange(nShapes), [targetShape]) # indices of distractors (all other indices)
winSizeCm = np.array((win.scrWidthCM*win.size[0]/win.scrWidthPIX, win.scrWidthCM*win.size[1]/win.scrWidthPIX)) # width and height in cm

# show target stimulus
visual.TextStim(win, text="Target stimulus", pos=(0, winSizeCm[1]/4), height=0.05*winSizeCm[1], wrapWidth=winSizeCm[0]).draw()
stimuli[0][targetShape].draw()
win.flip()
core.wait(3)

# set initial stimuli, half of them is not shown
for i, stimulus in enumerate(stimuli):
	resetStimulus(i, frame = 0, skipVisible = i<len(stimuli)//2)

## script, experiment
frame = 0
mouse.clickReset()
while not event.getKeys():
	# set state of stimuli
	for i, stimulus in enumerate(stimuli):
		if(frame<times[i][0]):
			stimulus[shapes[i]].draw()
		if(frame>=times[i][1]):
			target = np.random.random() < targetProbability and frame > targetAllowedTime
			resetStimulus(i, frame, target)

	# handle mouse events
	m = mouse.getPressed(getTime=True)
	if m[0][0]:
		if mState==0:
			print("click at frame {:d}".format(frame))
			mState += 1
		elif mState==2:
			print("click at position ({:6.1f},{:6.1f})".format(*mouse.getPos()))
			mState += 1
	else:
		if mState==1:
			mouse.setVisible(True)
			mState += 1
		elif mState==3:
			mouse.setVisible(False)
			mouse.clickReset()
			mState = 0

	win.flip()
	frame += 1
