from ONVIFCameraControl import ONVIFCameraControl  # import ONVIFCameraControlError to catch errors
from time import sleep

ip = '192.168.1.160'
port = 2000
usr = 'admin'
pwd = 'admin'

cam = ONVIFCameraControl((ip, port), usr, pwd)

ptz_velocity_vector = (1, 1, 1)


cam.goto_preset(0, ptz_velocity_vector)
