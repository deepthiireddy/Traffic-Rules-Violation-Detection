# import the necessary packages
import datetime
import time

import cv2
import imutils


# import winsound

class TrafficProcessor:

    def __init__(self, camera_id):
        self.firstFrame = None
        self.light = "Green"
        self.cnt = 0
        self.dynamic = False
        self.min_area = 500
        self.duration = 200  # millisecond
        self.freq = 900  # Hz

        if camera_id == 'cam_01':
            self.zone1 = (100, 150)
            self.zone2 = (450, 145)
            self.thres = 30

        elif camera_id == 'cam_02':
            self.zone1 = (100, 150)
            self.zone2 = (450, 145)
            self.thres = 6
            self.dynamic = True

    def cross_violation(self, frame):
        text = ""
        isCar = False
        cropped_cars = []  # list for taking all violated car's snap

        # resize the frame, convert it to grayscale, and blur it
        self.frame = imutils.resize(frame, width=500)
        self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        self.gray = cv2.GaussianBlur(self.gray, (21, 21), 0)

        # if the first frame is None, initialize it
        if self.firstFrame is None:
            self.firstFrame = self.gray
            pack = {'frame': self.frame, 'reference': self.firstFrame, 'list_of_cars': cropped_cars, 'cnt': self.cnt}
            return pack

        # compute the absolute difference between the current frame and
        # first frame
        self.frameDelta = cv2.absdiff(self.firstFrame, self.gray)
        self.thresh = cv2.threshold(self.frameDelta, self.thres, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        self.thresh = cv2.dilate(self.thresh, None, iterations=2)
        cnts = cv2.findContours(self.thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.min_area:
                continue

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            if ((x + w / 2) > self.zone1[0] and (x + w / 2) < self.zone2[0] and (y + h / 2) < self.zone1[1] + 100 and (
                    y + h / 2) > self.zone2[1] - 100):
                isCar = True

            if self.light == "Red" and (x + w / 2) > self.zone1[0] and (x + w / 2) < self.zone2[0] and (y + h / 2) < \
                    self.zone1[1] and (y + h / 2) > self.zone2[1]:
                # winsound.Beep(self.freq, self.duration)
                rcar = self.frame[y:y + h, x:x + w]
                rcar = cv2.resize(rcar, (0, 0), fx=4, fy=4)
                cropped_cars.append(rcar)
                cv2.imwrite('reported_car/reported_car_' + str(self.cnt) + ".jpg", rcar)
                self.cnt += 1
                text = "<Violation>"

            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (255, 255, 0), 2)

        if isCar == False or self.dynamic == True:
            self.firstFrame = self.gray
        # draw the text and timestamp on the frame
        color = (0, 0, 255)
        if self.light == "Green":
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)

        cv2.rectangle(self.frame, self.zone1, self.zone2, (255, 0, 0), 2)
        cv2.putText(self.frame, "Signal Status: {}".format(self.light), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.putText(self.frame, "{}".format(text), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.putText(self.frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, self.frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        pack = {'frame': self.frame, 'reference': self.firstFrame, 'list_of_cars': cropped_cars, 'cnt': self.cnt}

        return pack
#
#
# camera_name = 'cross001'  # name/id of the camera
#
# camera_scr = {'cross001': 'videos/video7.mp4',
#               'cross002': 'videos/video6.mp4'}  # key = camera_name/id , value = video_scr
#
# vs = cv2.VideoCapture(camera_scr[camera_name])
#
# sys = TrafficProcessor(camera_name)  # instance of violation class
#
# # loop over the frames of the video
# while True:
#     ret, frame = vs.read()
#     if ret == False:
#         break
#     # The function call for cross violation detection
#     packet = sys.cross_violation(frame)
#
#     show_frame = packet['frame']  # the live feed for the gui
#     cropped_car_images = packet['list_of_cars']  # list of cropped images of violated cars
#
#     cv2.imshow("Security Feed", show_frame)
#     time.sleep(.05)
#     if len(cropped_car_images) > 0: cv2.imshow("violated car", cropped_car_images[0])
#
#     key = cv2.waitKey(1) & 0xFF
#
#     # if the `q` key is pressed, break from the loop
#     if key == ord("q"):
#         break
#     # press 's' to switch traffic signal from green to red and vice-versa
#     elif key == ord("s"):
#         if sys.light == "Green":
#             sys.light = "Red"
#         elif sys.light == "Red":
#             sys.light = "Green"
#
# # cleanup the camera and close any open windows
# # vs.stop() if args.get("video", None) is None else vs.release()
# cv2.destroyAllWindows()
