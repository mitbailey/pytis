import ctypes
import libs.tisgrabber as tis
import signal
import sys
import time

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
    ic.IC_OpenVideoCaptureDevice(hGrabber, tis.T('DMK 33UX174'))

    # Check that the device was found.
    if not ic.IC_IsDevValid(hGrabber):
        ic.IC_MsgBox(tis.T('No device found.'), tis.T('Simple Live Video'))
        tis_clean_exit()
    
    # Manually set the video format and framerate.
    ic.IC_SetVideoFormat(hGrabber, tis.T('RGB32 (1920x1200)'))
    ic.IC_SetFrameRate(hGrabber, ctypes.c_float(150.0))
    # ic.IC_SetPropertyValue(hGrabber, )

    vmin = ctypes.c_float()
    vmax = ctypes.c_float()
    ic.IC_GetPropertyAbsoluteValueRange(hGrabber, tis.T("Exposure"), tis.T("Value"),
                                        vmin, vmax)
    print("Exposure range:", vmin, ' - ', vmax)

    ic.IC_GetPropertyAbsoluteValueRange(hGrabber, tis.T("Gain"), tis.T("Value"),
                                        vmin, vmax)
    print("Gain range:", vmin, ' - ', vmax)

    EXPOSURE = 1e-04
    GAIN = 0.0

    chkval = ctypes.c_float()
    retval = ic.IC_SetPropertyAbsoluteValue(hGrabber, tis.T("Exposure"), tis.T("Value"), ctypes.c_float(EXPOSURE))
    if retval != tis.IC_SUCCESS:
        print('Failed to set exposure:', retval)
    else:
        print('Exposure set to ', chkval)
        ic.IC_GetPropertyAbsoluteValue(hGrabber, tis.T('Exposure'), tis.T('Value'), chkval)

    ic.IC_SetPropertyAbsoluteValue(hGrabber, tis.T("Gain"), tis.T("Value"), ctypes.c_float(GAIN))
    if retval != tis.IC_SUCCESS:
        print('Failed to set gain:', retval)
    else:
        print('Gain set to ', chkval)
        ic.IC_GetPropertyAbsoluteValue(hGrabber, tis.T('Gain'), tis.T('Value'), chkval)
    
    ic.IC_StartLive(hGrabber, 0)
    # sleep(5)
    # exit(0)

    # num_shots = 5
    shot_time = 1000
    key = ''
    bat_num = 0
    while key != 'q':
        print('s: Snap & Save')
        print('c: Capture 10s (3s delay)')
        print('q: Quit')
        key = input('> ')
        
        img_num = 0
        if key == 's':
            print('Waiting...')
            time.sleep(1)
            print('SNAPPING!')
            t0 = time.time()
            t = 0
            while(t<1000):
                retval = ic.IC_SnapImage(hGrabber, 2000)
                if retval == tis.IC_SUCCESS:
                    t = int(1000*(time.time() - t0))
                    ic.IC_SaveImage(hGrabber, tis.T('data/snap_%03d_%03d_%06d.bmp'%(bat_num, img_num, t)), tis.ImageFileTypes['BMP'], 90)
                    # print('Image saved.')
                    img_num+=1
                else:
                    print('No frame received in 2 seconds.')
                    print(retval)
                    print('Cancelling, took %d shots.'%(img_num))
                    break
            bat_num+=1
        elif key == 'c':
            print('T-3...')
            time.sleep(1)
            print('T-2...')
            time.sleep(1)
            print('T-1...')
            time.sleep(1)
            print('SNAPPING!')
            t0 = time.time()
            t = 0
            while(t<10000):
                retval = ic.IC_SnapImage(hGrabber, 2000)
                if retval == tis.IC_SUCCESS:
                    t = int(1000*(time.time() - t0))
                    ic.IC_SaveImage(hGrabber, tis.T('data/snap_%03d_%03d_%06d.bmp'%(bat_num, img_num, t)), tis.ImageFileTypes['BMP'], 90)
                    # print('Image saved.')
                    img_num+=1
                else:
                    print('No frame received in 2 seconds.')
                    print(retval)
                    print('Cancelling, took %d shots.'%(img_num))
                    break
            bat_num+=1
        elif key == 'c2':
            print('T-3...')
            time.sleep(1)
            print('T-2...')
            time.sleep(1)
            print('T-1...')
            time.sleep(1)
            print('SNAPPING!')
            t0 = time.time()
            t = 0
            while(t<10000):
                retval = ic.IC_SnapImage(hGrabber, 2000)
                if retval == tis.IC_SUCCESS:
                    t = int(1000*(time.time() - t0))
                    ic.IC_SaveImage(hGrabber, tis.T('data/snap_%03d_%03d_%06d.bmp'%(bat_num, img_num, t)), tis.ImageFileTypes['BMP'], 90)
                    # print('Image saved.')
                    img_num+=1
                else:
                    print('No frame received in 2 seconds.')
                    print(retval)
                    print('Cancelling, took %d shots.'%(img_num))
                    break
            bat_num+=1

        time.sleep(0.1)

    tis_clean_exit();