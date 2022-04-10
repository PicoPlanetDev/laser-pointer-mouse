import cv2
import mouse
import keyboard

PROJECTOR_RESOLUTION_WIDTH = 1280 # The width of your projector
PROJECTOR_RESOLUTION_HEIGHT = 720 # The height of your projector

# If you are mirroring, just use 0. 
# Otherwise, figure out where your projector is compared to your 
# main monitor's top left. Negative values are allowed, and
# represent the projector being to the left of your main monitor.
# For example, my projector is to the right of my main monitor,
# and my main monitor has an X resolution of 1920, so I would
# set PROJECTOR_X_OFFSET to 1920.
# This represents the position of the left size of the projector.
# Not sure? Run print_position.py and move your mouse to the left side
# of the projector screen and use that X coordinate.
PROJECTOR_X_OFFSET = 1920
PROJECTOR_Y_OFFSET = 0 # Same as above, but for the Y axis.

CAMERA_INDEX = 0 # 0 indexed, often the built-in webcam on a laptop
LEFT_CLICK_MAPPING = 'down' # Figure out what your presenter's buttons use
RIGHT_CLICK_MAPPING = 'up' # Figure out what your presenter's buttons use


print("Starting...")

def calibrate():
    def onThresholdTrackbarChanged(value):
        pass

    def finish(dotsX, dotsY):
        threshold = cv2.getTrackbarPos("Threshold", "calibration")
        cv2.destroyWindow('calibration')

        lowXpos = min(dotsX)
        lowYpos = min(dotsY)
        highXpos = max(dotsX)
        highYpos = max(dotsY)
        return lowXpos, lowYpos, highXpos, highYpos, threshold


    cv2.namedWindow('calibration')

    cv2.createTrackbar('Threshold', 'calibration', 250, 255, onThresholdTrackbarChanged)

    print("Trace the corners of the screen and press 'f' when finished.")
    dotsX = []
    dotsY = []
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.inRange(gray, cv2.getTrackbarPos("Threshold", "calibration"), 255)

        contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5 and area < 100:
                x, y, w, h = cv2.boundingRect(contour)
                dotsX.append(x + w / 2)
                dotsY.append(y + h / 2)

        # Display the resulting frame
        cv2.imshow('calibration', thresh)

        if cv2.waitKey(1) == ord('f'):
            return finish(dotsX, dotsY)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 1280)
cap.set(4, 720)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

def preview():
    print("Press c to calibrate")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # Display the resulting frame
        cv2.imshow('preview', frame)

        if cv2.waitKey(1) == ord('c'):
            break
    
    main(calibrate())

def move_mouse(dotX, dotY, top_left, bottom_right):
    def get_size(top_left, bottom_right):
        return bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]

    def offset_laser_pos(dotX, dotY):
        return dotX - top_left[0], dotY - top_left[1]

    def translate_size(x, y, hsize, vsize, display_width, display_height):
        x = (x * display_width) / hsize
        y = (y * display_height) / vsize
        return x, y
        
    hsize, vsize = get_size(top_left, bottom_right)
    offsetX, offsetY = offset_laser_pos(dotX, dotY)
    x, y = translate_size(offsetX, offsetY, hsize, vsize, PROJECTOR_RESOLUTION_WIDTH, PROJECTOR_RESOLUTION_HEIGHT)
    mouse.move(x+PROJECTOR_X_OFFSET, y+PROJECTOR_Y_OFFSET, absolute=True, duration=0.1)

def main(calibration):
    keyboard.on_release_key(LEFT_CLICK_MAPPING, lambda: mouse.click(button='left'), suppress=True)
    keyboard.on_release_key(RIGHT_CLICK_MAPPING, lambda: mouse.click(button='right'), suppress=True)

    top_left = (int(calibration[0]), int(calibration[1]))
    bottom_right = (int(calibration[2]), int(calibration[3]))
    threshold = calibration[4]

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break

        output = frame.copy()

        # Process the image
        output = cv2.rectangle(output, top_left, bottom_right, (0,0,255), 2)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        thresh = cv2.inRange(gray, threshold, 255)

        dotX = []
        dotY = []
        contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5 and area < 100:
                x, y, w, h = cv2.boundingRect(contour)
                dotX.append(x + w / 2)
                dotY.append(y + h / 2)
        
        if len(dotX) == 1:
            move_mouse(dotX[0], dotY[0], top_left, bottom_right)

        cv2.imshow('preview', output)
        if cv2.waitKey(1) == ord('q'): break

preview()

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()