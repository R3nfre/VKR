import cv2
import torch
from PIL import Image
import numpy as np
import time

import threading
import pyttsx3

import winsound


# def makeSound(note, engine):
#     winsound.Beep(250, 250)
#     engine.say(note)
#     engine.runAndWait()


# Signs
signs = []
clks = []
note = ""
xclk = None
currentTime = None
miscurrentTime = None
xcanceled = ['3_20', '3_24', '3_27']
speedLimits = ['10', '20', '30', '40', '50', '60', '70', '80', '90', '100', '110', '120']
limitedRadius = ['1_8', '2_1', '2_4', '3_25', '3_31', '4_1_2', '4_2_3', '5_15_3', '5_15_5']
ignored = ['1_22', '1_23', '2_5', '3_2', '3_13', '3_32', '3_4_1', '4_1_1', '4_1_4', '4_2_1', '5_15_1', '5_15_2',
           '5_15_7', \
           '5_16', '5_19_1', '6_3_1', '7_3', '8_1_1']


# Models
model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:\\Users\\HP\\resources\\traffic.pt',
                       force_reload=True)
# numberModel = torch.hub.load('ultralytics/yolov5', 'custom', path='C:\\Users\\HP\\resources\\best.pt',
#                              force_reload=True)

# Sound
# engine = pyttsx3.init()
# engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0')
# engine.say("Система исправна")
# engine.runAndWait()

# Video for capture
video = cv2.VideoCapture("C:\\Users\\HP\\resources\\video.mp4")

while True:
    ret, frame = video.read()

    results = model(frame)
    signPrediction = results.pandas().xyxy[0]  # image predictions (pandas)

    # Frame skips
    # if signPrediction.empty == True:
    # continue

    for i in range(signPrediction.shape[0]):
        if signPrediction.loc[i][4] > 0.6:
            cv2.rectangle(frame, (int(signPrediction.xmin[i]), int(signPrediction.ymin[i])),
                          (int(signPrediction.xmax[i]), int(signPrediction.ymax[i])), (0, 255, 0), 2)
            cv2.putText(frame, signPrediction.name[i] + " (" + str(signPrediction.confidence[i]) + ")",
                        (int(signPrediction.xmin[i]), int(signPrediction.ymin[i])),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Speed limits
            if signPrediction.loc[i][6] == '3_24' and signPrediction.loc[i][4] > 0.65 and not currentTime:
                speedSign = 10
                speed = ''
                for j in range(speedSign.shape[0]):
                    # if speedSign.loc[j][4] > 0.5:
                    speed += str(speedSign.loc[j][6])

                if speed != '':
                    if int(speed) < int(speed[::-1]):
                        speed = speed[::-1]

                    # If result is correct, remove another speed limit and add the current one
                    if speed in speedLimits:
                        for sign in signs:
                            if sign in speedLimits:
                                if int(speed) - int(sign) > 0:
                                    note = "Максимальная скорость увеличилась на " + str(
                                        int(speed) - int(sign)) + " км/ч"
                                else:
                                    note = "Будьте внимательны! Максимальная скорость уменьшилась на " + str(
                                        int(sign) - int(speed)) + " км/ч!"
                                signs.remove(sign)
                            else:
                                note = "Ограничение скорости " + speed + " км/ч."
                        signs.append(speed)
                        currentTime = time.time()

            if signPrediction.loc[i][6] not in signs and signPrediction.loc[i][6] != '3_24':

                # Crossroads
                if signPrediction.loc[i][6] == '2_1' or signPrediction.loc[i][6] == '2_4':
                    if signPrediction.loc[i][4] > 0.8 and not xclk:
                        xclk = time.time()

                        for item in xcanceled:
                            if item in signs:
                                signs.remove(item)
                    else:
                        continue

                        # Copacity check for overtaking sign
                if signPrediction.loc[i][6] == '3_20' and signPrediction.loc[i][4] < 0.85:
                    continue
                # Remove overtaking sign cause of traffic lights
                if signPrediction.loc[i][6] == '1_8' and '3_20' in signs:
                    signs.remove('3_20')


                # End of speed limit
                elif signPrediction.loc[i][6] == '3_25':
                    for sign in signs:
                        if sign in speedLimits:
                            signs.remove(sign)

                # Ignore incorrect 5_15_3 detecting on turns
                elif signPrediction.loc[i][6] == '4_2_3':
                    if not miscurrentTime:
                        miscurrentTime = time.time()
                elif signPrediction.loc[i][6] == '5_15_3' and miscurrentTime:
                    continue
                # End of all limits
                # elif signPrediction.loc[i][6] == '3_31':

                # Ignored signs
                # add to the top condition (...and not in ignored)
                elif signPrediction.loc[i][6] in ignored:
                    continue

                # Add timer for signs with limited raduis
                if signPrediction.loc[i][6] in limitedRadius:
                    clks.append([signPrediction.loc[i][6], time.time()])

                # Add sign to the actual list
                signs.append(signPrediction.loc[i][6])

    # Check signs time actuality
    for i in range(len(clks)):
        if clks[i][1] + 10 < time.time():
            signs.remove(clks[i][0])
            clks.remove(clks[i])
            break
    if xclk and xclk + 30 < time.time():
        xclk = None
    if currentTime and currentTime + 3 < time.time():
        currentTime = None
    if miscurrentTime and miscurrentTime + 60 < time.time():
        miscurrentTime = None

    # Display signs
    if signs:
        for i in range(len(signs)):
            try:
                img = cv2.resize(
                    cv2.imread("C:\\Users\\HP\\resources\\" + str(signs[i]) + ".png"),
                    (80, 80))
                rows, cols, channels = img.shape
                frame[0:rows, 80 * i:cols + 80 * i] = img
                print(str(signs[i]))
            except:
                continue

    # Text to speak -- we'll send to thread only a phrase, the logic will be here
    if note:
        # t1 = threading.Thread(target=makeSound, args=(note, engine))  # create thread
        # t1.start()  # Launch created thread
        note = ""

    # print(Ь)

    cv2.imshow("video window", frame)
    if int(cv2.waitKey(30)) == 27:
        break

