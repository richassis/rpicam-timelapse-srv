from picamera.array import PiRGBArray
from picamera import PiCamera
from sys import argv
# get this with: pip install color_transfer
from color_transfer import color_transfer 

import time
import cv2

# init the camera
camera = PiCamera()
rawCapture = PiRGBArray(camera)

# camera to warmup
time.sleep(0.1)

# capture
camera.capture(rawCapture, format="bgr")
captured = rawCapture.array

# import the color source
color_source = cv2.imread(argv[1])

# transfer the color
result = color_transfer(color_source, captured,
                        clip=True, preserve_paper=False)

cv2.imwrite(argv[2], result)
