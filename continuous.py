import ctypes
import libs.tisgrabber as tis
import signal
import sys
from time import sleep

# DMK 33UX174
# https://www.theimagingsource.com/en-us/product/industrial/33u/dmk33ux174/
# Device driver required (Device Driver for USB 33U, 37U, 38U Cameras and DFG/HDMI Converter):
# https://www.theimagingsource.com/en-us/support/download/icwdmuvccamtis33u-5.1.0.1719/

ic = None
hGrabber = None

def sighandler(sig, frame):
    tis_clean_exit();
    print('Exiting gracefully.')

def tis_clean_exit():
    if ic is not None and hGrabber is not None:
        if ic.IC_IsLive(hGrabber):
            ic.IC_StopLive(hGrabber)
        ic.IC_ReleaseGrabber(hGrabber)
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler.
    signal.signal(signal.SIGINT, sighandler)

    # Load library.
    ic = ctypes.cdll.LoadLibrary('./libs/tisgrabber_x64.dll')
    tis.declareFunctions(ic)
    ic.IC_InitLibrary(0)
    
    # Find & open device automagically. 
    # hGrabber = tis.openDevice(ic)
    
    # Find & open device manually. 
    hGrabber = ic.IC_CreateGrabber()
    ic.IC_OpenVideoCaptureDevice(hGrabber, tis.T("DMK 33UX174"))

    # Check that the device was found.
    if not ic.IC_IsDevValid(hGrabber):
        ic.IC_MsgBox(tis.T('No device found.'), tis.T('Simple Live Video'))
        tis_clean_exit()
    
    # Manually set the video format and framerate.
    ic.IC_SetVideoFormat(hGrabber, tis.T('RGB32 (1920x1200)'))
    ic.IC_SetFrameRate(hGrabber, ctypes.c_float(144.0))
    
    ic.IC_StartLive(hGrabber, 1)

    exit(0)

    n = 0
    key = ''
    while key != 'q':
        print('s: Snap & Save')
        print('q: Quit')
        key = input('> ')
        
        if key == 's':
            retval = ic.IC_SnapImage(hGrabber, 2000)
            if retval == tis.IC_SUCCESS:
                ic.IC_SaveImage(hGrabber, tis.T('snap_%d.bmp'%(n)), tis.ImageFileTypes['BMP'], 90)
                print('Image saved.')
            else:
                print('No frame received in 2 seconds.')
                print(retval)

        sleep(0.1)

    tis_clean_exit();