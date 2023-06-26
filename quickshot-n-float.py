from __future__ import absolute_import, division, print_function
from builtins import *  # @UnusedWildImport

from time import sleep
from mcculw import ul
from mcculw.enums import CounterChannelType
from mcculw.device_info import DaqDeviceInfo
from mcculw.enums import InterfaceType

import ctypes
import libs.tisgrabber as tis
import signal
import sys
import time

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

def config_first_detected_device(board_num, dev_id_list=None):
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise Exception('Error: No DAQ devices found')

    print('Found', len(devices), 'DAQ device(s):')
    for device in devices:
        print('  ', device.product_name, ' (', device.unique_id, ') - ',
              'Device ID = ', device.product_id, sep='')

    device = devices[0]
    if dev_id_list:
        device = next((device for device in devices
                       if device.product_id in dev_id_list), None)
        if not device:
            err_str = 'Error: No DAQ device found in device ID list: '
            err_str += ','.join(str(dev_id) for dev_id in dev_id_list)
            raise Exception(err_str)

    # Add the first DAQ device to the UL with the specified board number
    ul.create_daq_device(board_num, device)

def pulse_begin(frequency: float, duty_cycle: float, timer_num: int):
    print('FREQ:', frequency, ',', 'DUTY:', duty_cycle, ',', 'TIMR:', timer_num)

    dev_id_list = []
    board_num = 0

    try:
        config_first_detected_device(board_num, dev_id_list)
        daq_dev_info = DaqDeviceInfo(board_num)
        
        if not daq_dev_info.supports_counters:
            raise Exception('ERROR: The DAQ device does not support counters.')
        
        print('\nActive DAQ device: ', daq_dev_info.product_name, ' (', daq_dev_info.unique_id, ')\n', sep='')

        ctr_info = daq_dev_info.get_ctr_info()

        # Find a pulse timer channel on the board.
        first_chan = next((channel for channel in ctr_info.chan_info
                           if channel.type == CounterChannelType.CTRPULSE),
                          None)

        if not first_chan:
            raise Exception('Error: The DAQ device does not support '
                            'pulse timers')
        
        # timer_num = first_chan.channel_num
        # frequency = (1.0 / (cadence_ms * 1e-3))
        # duty_cycle = (on_time_ns / (cadence_ms * 1e6))

        # Start the pulse timer output (optional parameters omitted)
        actual_frequency, actual_duty_cycle, _ = ul.pulse_out_start(
            board_num, timer_num, frequency, duty_cycle)

        print('\nRequested output:')
        print('%f Hz, %f duty ratio.'%(frequency, duty_cycle))
        print('%f ns on-time, %f ns (%f s) cadence.'%((1/frequency)*1e9*duty_cycle, (1/frequency)*1e9, (1/frequency)))

        # Print information about the output
        print('\nVerified output:')
        print('%f Hz, %f duty ratio.'%(actual_frequency, actual_duty_cycle))
        print('%f ns on-time, %f ns (%f s) cadence.'%((1/actual_frequency)*1e9*actual_duty_cycle, (1/actual_frequency)*1e9, (1/actual_frequency)))

    except Exception as e:
        print(e)
        raise Exception(e)
    finally:
        return board_num, timer_num 


def pulse_end(board_num, timer_num):
    # Stop the pulse timer output
    ul.pulse_out_stop(board_num, timer_num)
    print('Timer output stopped.')
    ul.release_daq_device(board_num)
        

    # Serial.println("\n[C] ---------------------- Charge Enable");
    # Serial.println("[F] ---------------------- Float Actuator");
    # Serial.println("[D] ---------------------- Discharge Enable");
    # Serial.println("[W] {Duration} {Delay} --- Increment Charge; Pulse Duration, Delay (mS)");
    # Serial.println("[S] {Duration} {Delay} --- Decrement Charge; Pulse Duration, Delay (mS)");

# TMR0 will be the Charge Enable pin.
# TMR1 will be the Discharge Enable pin.
# When 'enabled', will be outputting a PWM of 500 Hz @ 0.9999 duty ratio.

if __name__ == '__main__':
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

    command = 'N/A'
    status = 'FLOATING'
    notice = '\n'
    pulsing = False
    tmr0_live = False
    tmr1_live = False
    cadence_mode = True

    print('\nEnsure the following:')
    print('TMR0 ==> CHG_EN')
    print('TMR1 ==> DCHG_EN\n')

    TMR0: int = 0
    TMR1: int = 1

    CHG_EN: int = TMR0
    DCHG_EN: int = TMR1

    CD_FREQ = 500
    CD_DUTY = 0.9999

    # CADENCE INPUT MODE ==
    # FREQUENCY INPUT MODE 
    shot_time = 1000
    # command = ''
    bat_num = 0
    while(command != 'q'):
        img_num = 0
        print('\n=== %s=================================='%('CADENCE INPUT MODE ==' if cadence_mode else 'FREQUENCY INPUT MODE '))
        print('[U] ---------------------------------- Float & Capture')
        print('[Q] ---------------------------------- QUIT')

        print('\nPrevious command:    %s'%(command))
        print('Current status:      %s\n'%(status))

        print(notice)
        command = input('> ')
        toks = (command.strip()).split()

        if toks is None or len(toks) <= 0:
            notice = 'INPUT INVALID: Input blank.'
            continue
        
        if len(toks) == 2:
            _dist_ms = 1000
            frequency = (1.0 / ((_dist_ms * 1e-3)+(float(toks[1]) * 1e-9)))
            duty_cycle = (float(toks[1]) / (_dist_ms * 1e6))
        elif len(toks) == 3:
            if cadence_mode:
                frequency = (1.0 / (float(toks[2]) * 1e-3))
                duty_cycle = (float(toks[1]) / (float(toks[2]) * 1e6))
            else:
                frequency = float(toks[1])
                duty_cycle = float(toks[2])

        # Always end the previous pulse(s).
        if tmr0_live:
            pulse_end(board_num, TMR0)
            tmr0_live = False
        if tmr1_live:
            pulse_end(board_num, TMR1)
            tmr1_live = False

        if toks[0] == 'F' or toks[0] == 'f':
            # Nothing further to do.
            status = 'FLOATING'
            pass

        elif toks[0] == 'C' or toks[0] == 'c':
            tmr0_live = True
            board_num, timer_num = pulse_begin(CD_FREQ, CD_DUTY, CHG_EN)
            status = 'CHARGING'
            pass
        
        elif toks[0] == 'D' or toks[0] == 'd':
            tmr1_live = True
            board_num, timer_num = pulse_begin(CD_FREQ, CD_DUTY, DCHG_EN)
            status = 'DISCHARGING'
            pass
        
        elif toks[0] == 'W' or toks[0] == 'w':
            board_num, timer_num = pulse_begin(frequency, duty_cycle, CHG_EN)
            sleep(0.5)
            pulse_end(board_num, CHG_EN)
            status = 'FLOATING (PULSED UP %.1f ns)'%(float(toks[1]))
            pass
        
        elif toks[0] == 'S' or toks[0] == 's':
            board_num, timer_num = pulse_begin(frequency, duty_cycle, DCHG_EN)
            sleep(0.5)
            pulse_end(board_num, DCHG_EN)
            status = 'FLOATING (PULSED DOWN %.1f ns)'%(float(toks[1]))
            pass
        
        elif toks[0] == 'WR' or toks[0] == 'wr':
            tmr0_live = True
            board_num, timer_num = pulse_begin(frequency, duty_cycle, CHG_EN)
            status = 'REPEAT PULSING UP (%.2f Hz @ %f)'%(frequency, duty_cycle)
            pass
        
        elif toks[0] == 'SR' or toks[0] == 'sr':
            tmr1_live = True
            board_num, timer_num = pulse_begin(frequency, duty_cycle, DCHG_EN)
            status = 'REPEAT PULSING DOWN (%.2f Hz @ %f)'%(frequency, duty_cycle)
            pass
        
        elif toks[0] == 'R' or toks[0] == 'r':
            cadence_mode = not cadence_mode
            pass

        elif toks[0] == 'U' or toks[0] == 'u': 
            print('CHARGING...')
            tmr0_live = True
            board_num, timer_num = pulse_begin(CD_FREQ, CD_DUTY, CHG_EN)

            print('T-3')
            time.sleep(1)
            print('T-2')
            time.sleep(1)
            print('T-1')
            time.sleep(1)
            print('CAPTURING & FLOATING...')

            charging = True

            t0 = time.time()
            t = 0
            while(t<10000):
                retval = ic.IC_SnapImage(hGrabber, 2000)

                # Wait some time before beginning the discharge.
                if charging and t > 500:
                    charging = False
                    if tmr0_live:
                        pulse_end(board_num, TMR0)
                        tmr0_live = False
                    if tmr1_live:
                        pulse_end(board_num, TMR1)
                        tmr1_live = False

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

            
            print('DONE.')
            status = 'FLOATING'
            pass

        else:
            continue
        
        continue