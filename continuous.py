import ctypes
import libs.tisgrabber as tis
import signal
import sys

ic = None
hGrabber = None

def sighandler(sig, frame):
    tis_cleanup();
    print('Exiting gracefully.')

def tis_cleanup():
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
    ic.IC_OpenVideoCaptureDevice(hGrabber, tis.T("DFK Z30GP031"))

    # Check that the device was found.
    if not ic.IC_IsDevValid(hGrabber):
        ic.IC_MsgBox(tis.T('No device found.'), tis.T('Simple Live Video'))
    
    # Manually set the video format and framerate.
    ic.IC_SetVideoFormat(hGrabber, tis.T('RGB32 (640x480)'))
    ic.IC_SetFrameRate(hGrabber, ctypes.c_float(30.0))
    
    ic.IC_StartLive(hGrabber, 1)

    n = 0
    key = ''
    while key != 'q':
        print('s: Snap & Save')
        print('q: Quit')
        key = input('> ')
        
        if key == 's':
            if ic.IC_SnapImage(hGrabber, 2000) == tis.IC_SUCCESS:
                ic.IC_SaveImage(hGrabber, tis.T('snap_%d.bmp'%(n)), tis.ImageFileTypes['BMP'], 90)
                print('Image saved.')
            else:
                print('No frame received in 2 seconds.')

    tis_cleanup();