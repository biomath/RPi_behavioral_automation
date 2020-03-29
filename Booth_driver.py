import RPi.GPIO as GPIO
import sys
import re
from datetime import datetime, timedelta
from Booth import *

__author__ = 'Matheus Macedo-Lima'
__version__ = '04/28/2019'

if __name__ == "__main__":
    """
    This file is a driver for Booth.py and should be run as sudo python Booth_driver_4.py
    Booth.py should not be run directly.
    """

    try:
        import readline
    except:
        pass  # readline not available

    def test_sound(sound):
        pg.mixer.init()
        pg.mixer.music.load(sound)
        pg.mixer.quit()

    def test_scene_files(path):
        # Cycle through files identifying their SNR and testing them
        file_names = glob(path + r'/*.wav')
        print "Testing sound files..."
        for file_name in file_names:
            # Files are formatted as Song1Pk43(-4)5snr.wav
            short_file_name = re.split("/", file_name)[-1]
            snr_value = int(re.findall(r'-?\d+', re.split("\)", short_file_name)[1])[0])
            try:
                print "Testing file " + short_file_name + " with SNR/dB = " + str(snr_value) + "...",
                test_sound(file_name)
            except pg.error:
                print pg.get_error()
                continue
            print " OK!"



    def timer_delay(delay):
        time_end = time.time() + delay
        while time.time() < time_end:
            sys.stdout.write("\rCountdown: " + str(round(time_end - time.time(), 0)) + " s")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\nStarting protocol...\n")
        sys.stdout.flush()
 
    # is_debug = raw_input("Debug session? (y/n)")
    is_debug = "n"
    if is_debug is "y":
        while True:
            protocol = raw_input("Test what protocol? Switch test(1), Introduction (2), Shaping (3), Go/No-go (4): ")
            session = Booth("debug")
            try:
                if protocol is "1":
                    session.switch_test()
                elif protocol is "2":
                    session.introduction()
                elif protocol is "3":
                    session.shaping()
                elif protocol is "4":
                    go_sound = raw_input("Go sound file name: ")
                    nogo_sound = raw_input("No-go sound file name: ")
                    session.go_nogo(go_sound=go_sound, nogo_sound=nogo_sound)
            except KeyboardInterrupt:
                GPIO.cleanup()
                exit_or_rerun = raw_input("Exit (1) or Rerun (2)? ")
                if exit_or_rerun is "1":
                    exit()
                elif exit_or_rerun is "2":
                    del session
                    continue
    elif is_debug is "n":
        while True:
            try:
                repeat = raw_input("Do you wish to repeat this protocol at the same time every day? (y/n): ")
                if repeat is "y":
                    injection = raw_input("Is this an injection protocol? (y/n): ")
                protocol = raw_input("Choose protocol: Switch test(1), Introduction (2), Shaping (3), "
                                     "Go/No-go (4), Scene discrimination (5), Classical->Operant Go/No-go (6): ")
                session_id = raw_input("Session ID (subject_YYMMDD for daily repetitions): ")
                duration = None
                delay = None
                go_sound = None
                nogo_sound = None
                wn_sound = None
                prob = None
                go_path = None
                nogo_path = None
                block_size = None
                classical_probability = None
                classical_iti_range = None
                classical_trial_cap = None
                operant_probability = None
                operant_trial_cap = None
                if protocol is "1":
                    session = Booth(session_id)
                    session.switch_test()
                elif protocol is "2":
                    session = Booth(session_id)
                    duration = int(raw_input("Duration of the trial (in seconds)? (eg 4h = 14400 s; 11h = 39600): "))
                    delay = float(raw_input("How long before the start of the trial (in seconds)? "))
                    prompt = raw_input("Press enter to start timer.")
                    timer_delay(delay)
                    session.introduction(duration=duration)
                elif protocol is "3":
                    session = Booth(session_id)
                    duration = int(raw_input("Duration of the trial (in seconds)? (eg 4h = 14400 s; 11h = 39600): "))
                    delay = float(raw_input("How long before the start of the trial (in seconds)? "))
                    prompt = raw_input("Press enter to start timer.")
                    timer_delay(delay)
                    session.shaping(duration=duration)
                elif protocol is "4":
                    go_sound = raw_input("Go sound file name: ")
                    try:
                        test_sound(go_sound)
                    except pg.error:
                        print pg.get_error()
                        continue
                    nogo_sound = raw_input("No-go sound file name: ")
                    try:
                        test_sound(nogo_sound)
                    except pg.error:
                        print pg.get_error()
                        continue
                    # wn_sound = raw_input("White noise sound file name: ")
                    wn_sound = "GNG_WN.wav"
                    try:
                        test_sound(wn_sound)
                    except pg.error:
                        print pg.get_error()
                        continue                    

                    prob = float(raw_input("Probability of go trial (0-100):"))/100
                    duration = int(raw_input("Duration of the trial (in seconds)? (eg 4h = 14400 s; 11h = 39600): "))
                    delay = float(raw_input("How long before the start of the trial (in seconds)? "))
                    prompt = raw_input("Press enter to start timer.")

                    timer_delay(delay)
                    session = Booth(session_id)
                    session.go_nogo(go_sound=go_sound, nogo_sound=nogo_sound, probability=prob, duration=duration)
                elif protocol is "5":
                    go_path = raw_input("Folder path with GO sounds: ")

                    test_scene_files(go_path)

                    nogo_path = raw_input("Folder path with NO-GO sounds: ")
                    test_scene_files(nogo_path)

                    # wn_sound = raw_input("White noise sound file name: ")
                    wn_sound = "GNG_WN.wav"
                    try:
                        test_sound(wn_sound)
                    except pg.error:
                        print pg.get_error()
                        continue

                elif protocol is "6":
                    go_sound = raw_input("Go sound file name: ")
                    try:
                        test_sound(go_sound)
                    except pg.error:
                        print pg.get_error()
                        continue
                    nogo_sound = raw_input("No-go sound file name: ")
                    try:
                        test_sound(nogo_sound)
                    except pg.error:
                        print pg.get_error()
                        continue
                    # wn_sound = raw_input("White noise sound file name: ")
                    wn_sound = "GNG_WN.wav"
                    try:
                        test_sound(wn_sound)
                    except pg.error:
                        print pg.get_error()
                        continue

                    classical_probability = \
                        float(raw_input("Probability of go trial in classical conditioning (0-100):"))/100
                    classical_trial_cap = int(
                        raw_input("Number of trials in classical conditioning: "))
                    classical_iti_range = (30, 60)  # fixed for now
                    operant_probability = \
                        float(raw_input("Probability of go trial in Operant conditioning (0-100):"))/100
                    operant_trial_cap = int(
                        raw_input("Maximum trials in operant conditioning: "))

                    duration = float(
                        raw_input("Maximum total duration of the trial (in seconds)? (eg 4h = 14400 s; 11h = 39600): "))

                    delay = float(raw_input("How long before the start of the trial (in seconds)? "))
                    prompt = raw_input("Press enter to start timer.")

                    timer_delay(delay)
                    session = Booth(session_id)
                    session.classical_to_operant_conditioning(
                        go_sound=go_sound, nogo_sound=nogo_sound, wn_sound=wn_sound,
                        classical_probability=classical_probability, operant_probability=operant_probability,
                        iti_range=classical_iti_range,
                        classical_conditioning_trial_cap=classical_trial_cap,
                        operant_conditioning_trial_cap=operant_trial_cap,
                        max_trial_duration=duration)

                del session
                GPIO.cleanup()

                if repeat is "y":
                    while True:
                        if injection is "n":
                            print "Timer before next session:"
                            timer_delay(86400 - duration)  # 24 hours minus previous duration
                        else:
                            prompt = raw_input("Press enter to start the" + str(delay) + " seconds timer...")

                            timer_delay(delay)

                        try:  # Session has a date as a second item
                            split_session = re.split("_*_", session_id)
                            current_day = datetime.strptime(split_session[1], '%y%m%d')
                            next_day = current_day + timedelta(days=1)
                            split_session[1] = datetime.strftime(next_day, '%y%m%d')

                            session_id = "_".join(split_session)
                        except (ValueError, IndexError):
                            split_session = re.split("_*_", session_id)
                            try:  # Session has a date as the last item (automatically set). Update it
                                current_day = datetime.strptime(split_session[-1], '%y%m%d')
                                next_day = current_day + timedelta(days=1)
                                split_session[-1] = datetime.strftime(next_day, '%y%m%d')
                                session_id = "_".join(split_session)
                            except ValueError:  # Session does not have a date. Add one at the end
                                session_id = session_id + "_" + datetime.strftime(datetime.now(), '%y%m%d')

                        session = Booth(session_id)

                        if protocol is "2":
                            session.introduction()
                        elif protocol is "3":
                            session.shaping(duration=duration)
                        elif protocol is "4":
                            session.go_nogo(go_sound=go_sound, nogo_sound=nogo_sound, probability=prob, duration=duration)
                        elif protocol is "5":
                            session.scene_discrimination(go_path, nogo_path, wn_sound=wn_sound, block_size=block_size,
                                                         probability=prob, duration=duration)
                        elif protocol is "6":
                            session.classical_to_operant_conditioning(
                                go_sound=go_sound, nogo_sound=nogo_sound, wn_sound=wn_sound,
                                classical_probability=classical_probability, operant_probability=operant_probability,
                                iti_range=classical_iti_range,
                                classical_conditioning_trial_cap=classical_trial_cap,
                                operant_conditioning_trial_cap=operant_trial_cap,
                                max_trial_duration=duration)

                        del session
                        GPIO.cleanup()

            except KeyboardInterrupt:
                GPIO.cleanup()
                exit_or_rerun = raw_input("Exit (1) or Rerun (2)? ")
                if exit_or_rerun is "1":
                    exit()
                elif exit_or_rerun is "2":
                    try:
                        del session
                    except NameError:
                        continue
