import time
import os
import sys
import threading
import math

speedscale = 0.4
targetheight = 150 #cm
isheadless = False
FlightIsReal = False
looping = True 
startedloop = False # true when started loop
DroneIsFlying = False
drone = None

    

#-ESTABLISH Bluetooth Connection-----------------------------------

os.system("sudo wpa_cli disconnect")
import bluetooth
import select
BTrunning = True
DispText = "Starting..."
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 1
server_socket.bind(("", port))
server_socket.listen(1)
print("Waiting for bluetooth connection...")
ready_to_read, _, _ = select.select([server_socket], [], [], 60)
if not ready_to_read:
    print("No connection within the timeout period. Aborting.")
    server_socket.close()
    sys.exit()
client_socket, client_info = server_socket.accept()
print("Accepted connection from", client_info)

def Report(mes):
    Mes = "[Program]: " + mes
    Mes += "\n"
    print(Mes)
    global BTrunning
    if BTrunning:
        client_socket.send(Mes.encode("utf-8"))
    global DispText
    DispText = mes

Report("Connected to program via Bluetooth")

BTrec = ""

def BTthreadDef():
    global BTrunning
    global looping
    global startedloop
    while BTrunning:
        try:
            bdata = client_socket.recv(1024).decode("utf-8").strip()
            print(bdata)
            #if not bdata:
                #break
            global BTrec
            BTrec = bdata
            if bdata == "stop" and not startedloop:
                looping = False
                Report("Initiated STOP command.")
                Report("(Loop has not started yet).")
                Report("Program Ended.")
                BTrunning = False
                client_socket.close()
                server_socket.close()
            if bdata == "stop" and startedloop:
                looping = False
                Report("Initiated STOP command.")
                
        except:
            looping = False
            print("ERROR: Disconnection in Bluetooth.")
            print("Aborting the program...")
            if DroneIsFlying:
                Report("Landing the drone...")
            if FlightIsReal:
                if DroneIsFlying:
                    Report("<Real Landing>")
                    drone.land()
                drone.end()
            BTrunning = False
            time.sleep(0.5)
            client_socket.close()
            server_socket.close()
            cap.release()
            cv2.destroyAllWindows()    
        finally:
            None
    print("Thread for Bluetooth has ended")

threadBT = threading.Thread(target=BTthreadDef)
threadBT.start()


# Check Real Flight

Report("1: Real Flight  2: No")
while True:
    if BTrec == "1":
        Report("Doing real flight.")
        isheadless = True
        FlightIsReal = True
        from djitellopy import Tello
        drone = Tello()
        break
    elif BTrec == "2":
        Report("Not doing real flight.")
        break

Report("Altitude (cm): ")
BTrec = ""
while True:
    if not BTrec == "":
        targetheight = eval(BTrec)
        Report(f"Target altitude: {targetheight}")
        break


#Time Variables
time_start = time.time()
time_last = time_start
time_lastmaxID = time.time()
t_det = 0
t_whole = 1

def getTime():
    global time_last
    timedif = time.time() - time_last
    time_last = time.time()
    return timedif

Report("Importing CV2...")
import cv2
import cv2.aruco as aruco
cv2time = round(getTime(), 3)
Report(f"CV2 Setup Time: {cv2time} sec.")

if not looping:
    raise SystemExit

import numpy as np
from simple_pid import PID

#Video Setup
resHeight = 240#480
resWidth = 320#640
_FPS = 12

#Camera Setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, _FPS)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, resWidth)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resHeight)

#ArUco
aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_250)
parameters = aruco.DetectorParameters_create()

#Other Variables
TargetID = 1
Treshold = 25
reachedID = 0
maxID = 0
pastTargetID = None

#Phase Variables
TakingOff = False
Navigating = True
Landing = False

#Aux
font = cv2.FONT_HERSHEY_SIMPLEX

# Controls
TargetX = resWidth / 2
TargetY = resHeight * 0.8

kii = 0.1
kdd = 0.15

kpx, kix, kdx = 1.5, kii, kdd 
kpy, kiy, kdy = 1.0, kii, kdd

pidx = PID(Kp=kpx, Ki=kix, Kd=kdx, setpoint=0)
pidy = PID(Kp=kpy, Ki=kiy, Kd=kdy, setpoint=0)
pidr = PID(Kp=0.8, Ki=0, Kd=0.0, setpoint=0)



# ESTABLISH Tello Connection


def check_wifi_connection(ssid):
    cmd = "iwgetid | grep -o '{}'".format(ssid)
    result = os.system(cmd)
    return result == 0

def connect_to_wifi(ssid):
    cmd = "sudo nmcli d wifi connect '{}'".format(ssid)
    os.system(cmd)

error_connect = 0
max_error_connect = 10
wifi_ssid = "TELLO-F27208"

if FlightIsReal:
    while not check_wifi_connection(wifi_ssid):
        Report("Not connected to {}... Trying to connect...".format(wifi_ssid))
        connect_to_wifi(wifi_ssid)
        time.sleep(5)
        error_connect += 1
        if error_connect > max_error_connect:
            Report("cancelling..")
            sys.exit()
            break
    Report("wifi_connected")
    drone.connect()
    Report("drone is_connected")
    batteryperc = drone.get_battery()
    Report(f"Drone Battery: {batteryperc}")

# Video Record
# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can choose other codecs as well
output_video = cv2.VideoWriter('/home/jake/Desktop/OutputVideos/output_video.mp4', fourcc, _FPS, (resWidth, resHeight))




dheight = targetheight
if FlightIsReal:
    dheight = drone.get_height()
startedloop = True
maxIDTimeReset = 5
maxIDTimer = 0
conX, conY, conR = 0, 0, 0
rl, fb, ud, cc = 0, 0, 0, 0
Mphase = 0
TimeSeenTarget = time.time()
TotalFrameTimeStart = 0.0
TotalFrame = 0
pastTotalFrame = 0
TotalFrameTime = 0
pastTotalFrameTime = 0
AveInfTime = 0
pos_array = np.empty((0,5))
timerecord = time.time()

try:
#if True:
    if looping:
        Report("Drone is taking off...")
        DroneIsFlying = True
        if FlightIsReal:
            Report("<Real Takeoff>")
            drone.takeoff()
        Report("Starting the loop...")
        pidx.reset()
        pidy.reset()
        pidr.reset()
        Report(f"ky: {kpy} {kiy} {kdy}")
        Report(f"kx: {kpx} {kix} {kdx}")

#----------------------------------------------------------------------------  
    while looping: 
         
        #if BTrec == "stop":
            #Report("Initiated STOP command.")
            #looping = False
        if BTrec == "height":
            if FlightIsReal:
                h = drone.get_height()
                Report(f"Height: {h}")

        TotalFrame += 1
        if TotalFrameTimeStart == -1:
            TotalFrameTimeStart = time.time()
        if TotalFrameTimeStart > 0:
            TotalFrameTime = time.time() - TotalFrameTimeStart
            
        time_start = time.time()
        t_pre = round(getTime(), 3) * 1000
        
        ret, image = cap.read()
        t_cap = round(getTime(), 3) * 1000
        
        #image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #image = cv2.GaussianBlur(image, (5, 5), 0)
        
        if image is not None:

            maxIDTimer = maxIDTimeReset - (time.time() - time_lastmaxID)
            if round(maxIDTimer, 1) <= 0  and TargetID > 0:
                maxID = reachedID
                maxIDTimer = 0

            if Mphase > 0: # altitude already reached
                # for one-time per target ID prompt
                if pastTargetID is None and TargetID is not None:
                    #Report(f"Target ID: {TargetID}")
                    Report(f"Aligning to ID: {TargetID} ...")
                    pidr.reset()
                    conR = 0
                elif TargetID != pastTargetID:
                    #Report(f"Target ID: {TargetID}")
                    Report(f"Aligning to ID: {TargetID} ...")
                # for height maintenance
                if FlightIsReal:
                    dheight = drone.get_height()
                    if dheight > targetheight + 4:
                        ud = -20
                    elif dheight < targetheight - 4:
                        ud = 20
                    else:
                        dheight = 0
                        

            pastTargetID = TargetID

            if Mphase == 0:
                extrah = 3
                if ud == 0:
                    Report(f"throttling to height: {targetheight / 100} m...")
                if FlightIsReal:
                    dheight = drone.get_height()
                else:
                    dheight = targetheight
                if dheight > targetheight + extrah:
                    ud = -speedscale * 100
                elif dheight < targetheight - extrah:
                    ud = speedscale * 100
                else:
                    ud = 0
                    Mphase = 1
                    Report(f"Target height: {targetheight} reached.")
                        
                ud = int(ud)
                cc = 0
                fb = 0
                rl = 0
                pidx.reset()
                pidy.reset()
                pidr.reset()
                TimeSeenTarget = time.time()
            
            # MArker Detection
            corners, ids, rejecteds = aruco.detectMarkers(image, aruco_dict, parameters=parameters)
            t_det = round(getTime(), 3) * 1000
            if ids is not None:
                
                aruco.drawDetectedMarkers(image, corners, ids)

                TargetIDIndex = None
                ind = 0
                
                # Find target ID
                for id in ids:
                    if id >= maxID:
                        maxID = id
                        time_lastmaxID = time.time()
                    if TargetID == 0 and id == reachedID + 1:
                        TargetID = id
                    if id == 0 and TargetID > maxID:
                        TargetIDIndex = ind
                        TargetID = 0
                        break
                    if id == TargetID:
                        TargetIDIndex = ind
                    ind += 1

                # Target ID indicator
                if TargetIDIndex is not None: # target ID has index in list of ID's, so presesnt

                    TimeSeenTarget = time.time()
                    pointA = corners[TargetIDIndex][0, 0]
                    pointB = corners[TargetIDIndex][0, 1]
                    pointC = corners[TargetIDIndex][0, 2]
                    pointD = corners[TargetIDIndex][0, 3]

                    # Xmean -> x-axis location of the center of target marker
                    # Ymean -> y-axis location of the center of targer marker
                    Xmean = round((pointA[0] + pointB[0] + pointC[0] + pointD[0]) / 4)
                    Ymean = round((pointA[1] + pointB[1] + pointC[1] + pointD[1]) / 4)

                    # displacement of target ID from screen's target location
                    MarX = Xmean - TargetX  
                    MarY = TargetY - Ymean
                    Mar = math.sqrt((MarX**2)+(MarY**2))

                    #Record relative position
                    if TargetID > 1:
                        #try:
                        timeiter = time.time()-timerecord
                        timerecord = time.time()
                        addend_row = np.array([Mphase, timeiter, reachedID + 1, MarX, MarY], dtype=object)
                        pos_array = np.append(pos_array, addend_row)
                        
                    
                    if Mphase == 1 and Xmean < (TargetX) + Treshold and Xmean > (TargetX) - Treshold:
                        Mphase = 2
                        Report(f"Going to ID: {TargetID}")
                        pidx.reset()
                        pidy.reset()
                        pidr.reset()

                    # target location reached within treshold
                    if Xmean < (TargetX) + Treshold and Xmean > (TargetX) - Treshold and Ymean < (TargetY) + Treshold and Ymean > (TargetY) - Treshold:
                        if TargetID == 0:   # landing marker
                            Report("ID 0 reached.")
                            TotalFrameTime = pastTotalFrameTime
                            TotalFrame = pastTotalFrame
                            AveInfTime = round(TotalFrameTime / TotalFrame, 4)
                            Report(f"Total Time: {round(TotalFrameTime, 3)}")
                            Report(f"Average Inf Time: {AveInfTime}")
                            if FlightIsReal:
                                drone.send_rc_control(0, 0, 0, 0)
                                time.sleep(0.2)
                            break
                        else:
                            reachedID += 1
                            Report(f"Reached ID: {reachedID}")
                            if TargetID == 1:
                                Report("Start of navigation")
                                TotalFrameTimeStart = -1
                                TotalFrame = 0
                            elif TargetID > 0:
                                pastTotalFrameTime = time.time() - TotalFrameTimeStart
                                pastTotalFrame = TotalFrame
                            TargetID += 1
                            if FlightIsReal:
                                drone.send_rc_control(0, 0, 0, 0)
                            pidx.reset()
                            pidy.reset()
                            pidr.reset()
                        Mphase = 1

                    #scaleX = round(MarX / TargetX, 2) * 100
                    #scaleY = round(MarY / TargetY, 2) * 100
                    
                    inpX = int(100 * MarX / TargetX)
                    inpY = int(100 * MarY / TargetX)
                    if MarX == 0:
                        inpR = 0
                    else:
                        try: 
                            inpR = int(math.atan((MarX/MarY))*180 / math.pi)
                        except:
                            inpR = 0

                    inpX = min(max(inpX, -100), 100) * speedscale
                    inpY = min(max(inpY, -100), 100) * speedscale
                    inpR = min(max(inpR, -100), 100)
                    
                    conX = int(pidx(-inpX))
                    conY = int(pidy(-inpY))
                    conR = int(pidr(-inpR))

                    conX = int(min(conX, speedscale * 100))
                    conY = int(min(conY, speedscale * 100))
                    conR = min(conR, 100)


                    rotspeed = 50
                    if Mphase == 1:
                        fb = 0
                        rl = 0
                        if MarX > 0:
                            cc = rotspeed
                        elif MarX < 0:
                            cc = -rotspeed
                        else:
                            cc = 0
                    elif Mphase == 2:
                        cc = 0
                        fb = conY
                        rl = conX

                    #conX = inpX
                    #conY = inpY
                    
                    cv2.circle(image, (int(Xmean),int(Ymean)), 5, (0,0,255), 3)

                    
                    
                else: # Absent target ID
                    rl = 0
                    fb = 0
                    cc = 0
                    
                    
            else: # No Ids
                rl = 0
                fb = 0
                cc = 0

            if ids is None or TargetIDIndex is None:
                if time.time() - TimeSeenTarget > 3:
                        Report(f"Unable to find the Target ID: {TargetID}")
                        TimeSeenTarget = time.time()
            
                
            topleft = (int(TargetX - Treshold), int(TargetY - Treshold))
            bottomright = (int(TargetX + Treshold), int(TargetY + Treshold))
            cv2.rectangle(image, topleft, bottomright, (0,0,255), 2)
            
            if FlightIsReal:
                dheight = drone.get_height()
            
            cv2.putText(image, f"Target ID: {TargetID}", (25,25), font, 0.75, (0,255,0), 2)
            cv2.putText(image, f"Reach ID: {reachedID}", (25,50), font, 0.5, (0,255,0), 2)
            cv2.putText(image, f"{DispText}", (25,75), font, 0.5, (0,255,0), 2)
             
            cv2.putText(image, f"fps: {round(1000/t_whole, 2)}", (resWidth-100,25), font, 0.5, (0,255,0), 2)
            cv2.putText(image, f"alt: {round(dheight / 100, 1)} m", (resWidth-100,50), font, 0.5, (0,255,0), 2)
            cv2.putText(image, f"time: {round(TotalFrameTime, 2)} s", (resWidth-100,75), font, 0.5, (0,255,0), 2)
            
            cv2.putText(image, f"X: {rl}", (10,resHeight-60), font, 0.5, (0,255,0),2)
            cv2.putText(image, f"Y: {fb}", (10,resHeight-45), font, 0.5, (0,255,0),2)
            cv2.putText(image, f"R: {cc}", (10,resHeight-30), font, 0.5, (0,255,0),2)
            cv2.putText(image, f"Z: {ud}", (10,resHeight-15), font, 0.5, (0,255,0),2)

            cv2.putText(image, f"{kpx} {kix} {kdx}", (resWidth-110,resHeight-45), font, 0.5, (0,255,0),2)
            cv2.putText(image, f"{kpy} {kiy} {kdy}", (resWidth-110,resHeight-30), font, 0.5, (0,255,0),2)
            #cv2.putText(image, f"R: {cc}", (resWidth-100,resHeight-15), font, 0.5, (0,255,0),2)

            #cv2.putText(image, f"Max Seen: {maxID}", (25,50), font, 0.5, (0,255,0), 2)
            #cv2.putText(image, f"mIDt: {round(maxIDTimer, 1)}", (resWidth-100,50), font, 0.5, (0,255,0), 2)
                
            if not isheadless:  
                cv2.imshow("Drone Video", image)
        
                    
        else: # No image
            Report("no image")
            break

        if FlightIsReal:
            drone.send_rc_control(rl, int(fb), ud, cc)
        
        if ret:
            output_video.write(image)

        if not isheadless:
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                looping = False 
        
        t_whole = round((time.time() - time_start)*1000)
        #print(f"time: {t_whole} | cap: {t_cap} | det: {t_det}")

        
        
except Exception as e:
    Report(f"Exception: {e}.")
    
finally:
    None
#if True:

output_video.release()

looping = False
Report("Loop finished.")


if DroneIsFlying:
    Report("Landing the drone...")
if FlightIsReal:
    if DroneIsFlying:
        Report("<Real Landing>")
        drone.land()
    drone.end()
FinalFileName = f"/home/jake/Desktop/OutputVideos/output_video_{round(TotalFrameTime, 3)}_{AveInfTime}.mp4"
os.rename('/home/jake/Desktop/OutputVideos/output_video.mp4', FinalFileName)
csvname =  f"/home/jake/Desktop/OutputCSV/pos_{round(TotalFrameTime, 3)}_{AveInfTime}.csv"
np.savetxt(csvname, pos_array, delimiter=",") 
Report("Program ended.")
Report("Type 'stop' again to disconnect socket.")
BTrunning = False
threadBT.join
client_socket.close()
server_socket.close()
cap.release()
cv2.destroyAllWindows()
