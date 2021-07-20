import RPi.GPIO as GPIO
import time
import numpy as np
import pygame as pg
import csv
import re
from glob import glob

__author__ = 'Matheus Macedo-Lima'
__version__ = '04/28/19'


class Booth:
    def __init__(self, subject_paradigm_id):
        self.subject_paradigm_id = subject_paradigm_id  # use this to describe your

        GPIO.setmode(GPIO.BOARD)  # set up GPIO pin numeration to ordinal

        self.TIMER = 0

        # Assign times of each outcome (in seconds)
        self.REWARD_TIME = 6
        self.PUNISHMENT_TIME = 1  # duration of puff of air
        self.ITI_RANGE = [30, 60]
        self.RESPONSE_TIME = 2  # Response will depend on delay time.
        self.NULL_TIME = 6  # Wait time after a miss or correct rejection
        self.PUNISHMENT_NULL_TIME = 16  # Wait time after a punishment
        self.DELAY_TIME = 0  # Delay between end of tone and chance of response

        # Load sound file names. They can also be set in the functions
        self.GO_SOUND = "GO.wav"
        self.NOGO_SOUND = "NOGO.wav"
        self.WN_SOUND = "GNG_WN.wav"

        # Assign pins to hardware
        # self.LIGHTS_PIN_1 = 11
        # self.LIGHTS_PIN_2 = 12
        self.PUFFER_PIN = 11

        self.REWARD_PIN = 19
        self.SWITCH_PIN = 15
        self.LED_PIN = 16  # For visual cuing

        # Initiate the GPIO pins
        # GPIO.setup(self.LIGHTS_PIN_1, GPIO.OUT)
        # GPIO.output(self.LIGHTS_PIN_1, 1)
        # GPIO.setup(self.LIGHTS_PIN_2, GPIO.OUT)
        # GPIO.output(self.LIGHTS_PIN_2, 1)
        GPIO.setup(self.PUFFER_PIN, GPIO.OUT)
        GPIO.output(self.PUFFER_PIN, 1)
        GPIO.setup(self.REWARD_PIN, GPIO.OUT)
        GPIO.output(self.REWARD_PIN, 1)
        GPIO.setup(self.SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.LED_PIN, GPIO.OUT)
        GPIO.output(self.LED_PIN, 0)

    """
    Now a bunch of redundant helper functions for controlling the hardware follows.
    Depending on how you set it up, ON is pin=1 and OFF is pin=0, or the opposite.
    Then you only need to change it here in the helpers.
    """

    # # Methods for lights off punishment
    # def lights_on(self):
    #     GPIO.output(self.LIGHTS_PIN_1, 1)
    #     GPIO.output(self.LIGHTS_PIN_2, 1)
    #
    # def lights_off(self):
    #     GPIO.output(self.LIGHTS_PIN_1, 0)
    #     GPIO.output(self.LIGHTS_PIN_2, 0)

    # If visual cue is used
    def led_on(self):
        GPIO.output(self.LED_PIN, 1)

    def led_off(self):
        GPIO.output(self.LED_PIN, 0)

    def reward_on(self):
        GPIO.output(self.REWARD_PIN, 0)

    def reward_off(self):
        GPIO.output(self.REWARD_PIN, 1)

    def apply_reward(self, duration=None):
        if duration is None:
            duration = self.REWARD_TIME
        self.reward_on()
        time.sleep(duration)
        self.reward_off()

    def apply_punishment(self, duration=None, step_out=False, apply_wn_too=False):
        if step_out:
            GPIO.output(self.PUFFER_PIN, 0)
            self.step_out_prompt()
            GPIO.output(self.PUFFER_PIN, 1)
        else:
            if duration is None:
                duration = self.PUNISHMENT_TIME
            GPIO.output(self.PUFFER_PIN, 0)
        if apply_wn_too:
            self.play_sound(self.WN_SOUND)
            time.sleep(duration)
            GPIO.output(self.PUFFER_PIN, 1)

    def apply_sleep_punishment(self, duration=None, wn_sound=None, apply_wn_too=False):
        if duration is None:
            duration = self.PUNISHMENT_TIME
        self.led_off()
        if apply_wn_too:
            self.play_sound(wn_sound)
            time.sleep(duration)

    @staticmethod
    def write_csv(title, row):
        """This is a helper function for creating and writing data on a csv file"""
        file = open(title + '.csv', 'a')
        writer = csv.writer(file, delimiter=',')
        writer.writerow(row)
        file.close()

    """
    Functions for playing audio
    """

    @staticmethod
    def play_sound(sound):
        pg.mixer.init()
        pg.mixer.music.load(sound)  # Load go sound
        pg.mixer.music.play()
        while pg.mixer.music.get_busy():  # Keep on hold while playing
            continue
        pg.mixer.quit()

    def peck_prompt(self, duration=None, step_out=False):
        """
        Program waits for a peck forever or for a specified duration.
        Returns response time if pecked, and None otherwise.
        """
        if not step_out:  # Only turn led on if this is not a step-out check
            self.led_on()  # if visual cuing is used

        if duration is not None:
            start_time = time.time()
            current_time = 0
            while current_time < duration:
                if GPIO.input(self.SWITCH_PIN) == 0:
                    return current_time
                current_time = time.time() - start_time
            return None
        # If duration is not specified
        else:
            start_time = time.time()
            current_time = 0
            while True:
                if GPIO.input(self.SWITCH_PIN) == 0:
                    return current_time
                time.sleep(0.001)
                current_time = time.time() - start_time

    def switch_test(self):
        """This function is for troubleshooting the functionality of the switch"""
        while True:
            print "Unstuck"
            self.peck_prompt()
            stuck = self.peck_prompt(duration=0.05)
            if stuck is not None:
                print "Stuck?"
            self.step_out_prompt()

    def step_out_prompt(self):
        # Bird has to hop off the perch
        step_out_flag = 0
        time_out = 1
        while step_out_flag is not None:
            step_out_flag = self.peck_prompt(duration=time_out, step_out=True)
            if step_out_flag is not None:
                self.led_off()

    def apply_null_time(self, duration=None):
        if duration is None:
            duration = self.NULL_TIME
        self.led_off()
        time.sleep(duration)

    """
    Paradigms
    """

    def stationary_reward(self):
        self.reward_on()

    def introduction(self, duration=14400, iti_range=None, reward_time=None):
        """
        Introduction paradigm
        Akin to Gess et al., 2011
        Reward is delivered in random intervals in the specified intertrial interval (ITI) range
        Reward duration is settable. If no time is set, default REWARD_TIME is used
        A csv file with number of trials and time since the beginning is written
        Automatically stops after 4 h by default
        """
        if iti_range is None:
            iti_range = self.ITI_RANGE
        if reward_time is None:
            reward_time = self.REWARD_TIME

        trial = 1
        self.write_csv(self.subject_paradigm_id + '_introduction', ["Number_of_trials"] + ["Time.from_start"])
        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm
        t0 = time.time()
        current_time = 0
        while current_time < duration:
            # self.led_on()
            time.sleep(np.random.uniform(iti_range[0], iti_range[1]))
            self.apply_reward(reward_time)
            current_time = time.time() - t0
            self.write_csv(self.subject_paradigm_id + '_introduction', [trial] + [current_time])
            trial += 1
            # self.led_off()

        self.reward_off()  # just to make sure

    def shaping(self, duration=14400, reward_time=None):
        """
        Shaping paradigm
        Akin to Gess et  al., 2011
        Every peck delivers a reward for a settable time.
        If no time is set, the default REWARD_TIME is used
        A csv file with number of trials and peck times since the beginning is written
        """
        if reward_time is None:
            reward_time = self.REWARD_TIME

        self.write_csv(self.subject_paradigm_id + '_shaping', ["Trial_number"] + ["Time_s"])

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        pecks = 0
        t_start = time.time()
        current_time = 0
        while current_time <= duration:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            start_peck = self.peck_prompt(duration=(duration - current_time))  # Birds initiate all trials!
            current_time = time.time() - t_start
            if start_peck is not None:
                self.apply_reward(reward_time)
                pecks += 1
                self.write_csv(self.subject_paradigm_id + '_shaping', [pecks] + [current_time])
                # Bird has to hop off the perch to reenable switch
                self.step_out_prompt()
                self.apply_null_time()
        self.led_off()

    def shaping_two_pecks(self):
        """
        Modified shaping paradigm
        Bird has to peck twice at the switch in order to get a reward. There is no timeout between pecks,
        but there is a minimum interval of 2 s (rough duration of a song).
        It is used to encourage more pecking
        """
        t0 = time.time()
        self.write_csv(self.subject_paradigm_id + '_shaping_two_pecks', ["Trial_number"] + ["Time_first_s"] +
                       ["Time_second_s"])

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        pecks = 0

        while True:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            self.peck_prompt()  # Birds initiate all trials!
            time_first = time.time() - t0
            pecks += 1
            time.sleep(2)  # duration of a song
            self.peck_prompt()
            time_second = time.time() - t0
            pecks += 1
            if pecks % 2 == 0:
                self.apply_reward(self.REWARD_TIME)
                self.write_csv(self.subject_paradigm_id + '_shaping_two_pecks', [pecks] + [time_first] + [time_second])

            # Bird has to hop off the perch to reenable switch
            self.step_out_prompt()
            self.apply_null_time()

    def shaping_timed(self, response_time=None):
        """
        Modified shaping paradigm
        Bird has to peck twice at the switch in order to get a reward. There is a settable timeout, which defaults to
        RESPONSE_TIME.
        There is a minimum interval of 2 s (rough duration of a song).
        It is used to encourage faster double pecking
        """
        if response_time is None:
            response_time = self.RESPONSE_TIME

        t0 = time.time()
        self.write_csv(self.subject_paradigm_id + '_shaping_timed',
                       ["Trial_number"] + ["Time_first_s"] + ["Time_second_s"] + ["Reward"])

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        pecks = 0

        while True:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            self.peck_prompt()  # Birds initiate all trials!
            time_first = time.time() - t0
            pecks += 1

            time.sleep(2)  # duration of a song

            second_peck = self.peck_prompt(duration=response_time)  # prompt for a timed second peck

            if second_peck is not None:
                time_second = time.time() - t0
                pecks += 1
                self.write_csv(self.subject_paradigm_id + '_shaping_timed', [pecks] + [time_first] + [time_second] +
                               ["YES"])
                self.apply_reward(self.REWARD_TIME)

                # Bird has to hop off the perch to reenable switch
                self.step_out_prompt()
                self.apply_null_time()
            else:
                self.write_csv(self.subject_paradigm_id + '_shaping_timed', [pecks] + [time_first] + ["NA"] + ["NO"])

    def go_nogo(self, go_sound=None, nogo_sound=None, wn_sound=None, probability=0.5, duration=39600,
                max_response_time=None, reward_time=None, punishment_time=None, null_time=None, delay_time=None):
        """
        Go/No-go paradigm
        Akin Gess et al., 2011

        The basic logic is:
        Peck -> Go or No-go sound is played (probability is settable) -> response_time prompt -> Peck again -> outcome

        If Go sound plays -> Peck -> reward
                          -> No Peck -> Null time

        If No-go sound plays -> Peck -> punishment
                             -> No peck -> Null time
        """
        self.write_csv(self.subject_paradigm_id + '_go_nogo', ["Trial_number"] + ["Trial_type"] + ["Response_time_s"] +
                       ["Hit"] + ["Miss"] + ["Reject"] + ["False_alarm"] + ["Time_from_start"] + ["Stimulus"])

        # Set defaults if not specified
        if go_sound is None:
            go_sound = self.GO_SOUND
        if nogo_sound is None:
            nogo_sound = self.NOGO_SOUND
        if max_response_time is None:
            max_response_time = self.RESPONSE_TIME
        if reward_time is None:
            reward_time = self.REWARD_TIME
        if punishment_time is None:
            punishment_time = self.PUNISHMENT_TIME
        if null_time is None:
            null_time = self.NULL_TIME
        if delay_time is None:
            delay_time = self.DELAY_TIME
        if wn_sound is None:
            wn_sound = self.WN_SOUND

        # Flags
        go_trial = False
        nogo_trial = False

        trial_number = 1  # Trial counter

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        """
        This is the main loop
        """
        curr_stimulus = ""
        time_start = time.time()
        current_time = 0
        while current_time <= duration:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            # Birds initiate all trials!
            start_peck = self.peck_prompt(duration=(duration - current_time))  # Birds initiate all trials!

            if start_peck is not None:
                # Choose Go or No-go song depending on the probability
                if np.random.binomial(1, probability) == 1:
                    self.play_sound(go_sound)
                    curr_stimulus = go_sound
                    go_trial = True

                else:
                    self.play_sound(nogo_sound)
                    curr_stimulus = nogo_sound
                    nogo_trial = True

                time.sleep(delay_time)

                if go_trial:
                    t0 = time.time()  # Registers current time
                    response_time = self.peck_prompt(duration=max_response_time)
                    if response_time is not None:  # Hit! :)
                        self.write_csv(self.subject_paradigm_id + '_go_nogo',
                                       [trial_number] + ["GO"] + [response_time] + [1] + [0] * 3 +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_reward(duration=reward_time)
                    else:  # Miss :(
                        self.write_csv(self.subject_paradigm_id + '_go_nogo',
                                       [trial_number] + ["GO"] + ["NA"] + [0] + [1] + [0] * 2 +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_null_time(duration=null_time)
                    go_trial = False

                if nogo_trial:
                    t0 = time.time()
                    response_time = self.peck_prompt(duration=max_response_time)
                    if response_time is not None:  # False alarm :(
                        self.write_csv(self.subject_paradigm_id + '_go_nogo',
                                       [trial_number] + ["NOGO"] + [response_time] + [0] * 3 + [1] +
                                       [t0 - time_start] + [curr_stimulus])
                        # self.apply_punishment()
                        self.apply_sleep_punishment(16, wn_sound=wn_sound,
                                                    apply_wn_too=True)  # Some birds might feel "demotivated" with harsh punishment...
                    else:  # Correct rejection! :)
                        self.write_csv(self.subject_paradigm_id + '_go_nogo',
                                       [trial_number] + ["NOGO"] + ["NA"] + [0] * 2 + [1] + [0] +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_null_time(duration=null_time)
                    nogo_trial = False
                trial_number += 1
                # Bird has to hop off the perch to reactivate switch
                self.step_out_prompt()

            current_time = time.time() - time_start

    def scene_discrimination(self, go_path, nogo_path, wn_sound=None, block_size=60,
                             probability=0.5, duration=14400,
                             max_response_time=None, reward_time=None, punishment_time=None, null_time=None,
                             delay_time=None):
        """
        Modified from Schneider and Woolley, 2013. Neuron
        Stimuli of different SNRs/intensities are presorted as a block. Once the block finishes, a new block is
        sorted.
        """

        def sort_stimulus_block(go_path, nogo_path, block_size):
            go_files = glob(go_path + r'/*.wav')  # there are 6 files in each path
            nogo_files = glob(nogo_path + r'/*.wav')

            rep_go_files = np.repeat(go_files, (block_size / 2) / len(go_files))
            rep_nogo_files = np.repeat(nogo_files, (block_size / 2) / len(nogo_files))

            ordered_concat = np.append(rep_go_files, rep_nogo_files)

            concat_block_indices = np.arange(0, len(ordered_concat))
            np.random.shuffle(concat_block_indices)
            return ordered_concat, concat_block_indices  # indices higher than block_size/2 are nogo

        file_identifier = self.subject_paradigm_id + '_scene'
        self.write_csv(file_identifier, ["Trial_number"] + ["Trial_type"] + ["Sound_file"] + ["Trial SNR/dB"]
                       + ["Response_time_s"] +
                       ["Hit"] + ["Miss"] + ["Reject"] + ["False_alarm"] + ["Time_from_start"])

        # Set defaults if not specified
        if max_response_time is None:
            max_response_time = self.RESPONSE_TIME
        if reward_time is None:
            reward_time = self.REWARD_TIME
        if punishment_time is None:
            punishment_time = self.PUNISHMENT_TIME
        if null_time is None:
            null_time = self.NULL_TIME
        if delay_time is None:
            delay_time = self.DELAY_TIME
        if wn_sound is None:
            wn_sound = self.WN_SOUND

        # Flags
        go_trial = False
        nogo_trial = False

        trial_number = 1  # Trial counter
        block_counter = 1  # keep track of how many blocks of sounds needed to be preshuffled
        block_index = 0
        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        """
        This is the main loop
        """
        time_start = time.time()
        current_time = 0
        while current_time <= duration:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)

            curr_block, shuffled_indices = sort_stimulus_block(go_path, nogo_path, block_size)
            block_index = 0
            while trial_number < len(curr_block) * block_counter:
                # Birds initiate all trials!
                start_peck = self.peck_prompt(duration=(duration - current_time))  # Birds initiate all trials!

                if start_peck is not None:
                    # Play cur_sound in the pre shuffled list based on the trial number
                    cur_sound_file = curr_block[shuffled_indices[block_index]]
                    cur_short_sound_file_name = re.split("/", cur_sound_file)[-1]
                    snr_value = int(re.findall(r'-?\d+', re.split("\)", cur_short_sound_file_name)[1])[0])

                    self.play_sound(cur_sound_file)
                    if shuffled_indices[block_index] < block_size / 2:
                        go_trial = True
                    else:
                        nogo_trial = True

                    time.sleep(delay_time)

                    if go_trial:
                        t0 = time.time()  # Registers current time
                        response_time = self.peck_prompt(duration=max_response_time)
                        if response_time is not None:  # Hit! :)
                            # ["Trial_number"] + ["Trial_type"] + ["Sound_file"] + ["Trial SNR/dB"]
                            # + ["Response_time_s"] +
                            # ["Hit"] + ["Miss"] + ["Reject"] + ["False_alarm"] + ["Time_from_start"]

                            self.write_csv(file_identifier,
                                           [trial_number] + ["GO"] + [cur_short_sound_file_name] + [snr_value] +
                                           [response_time] +
                                           [1] + [0] * 3 +  # 1, 0, 0, 0
                                           [t0 - time_start])
                            self.apply_reward(duration=reward_time)
                        else:  # Miss :(
                            self.write_csv(file_identifier,
                                           [trial_number] + ["GO"] + [cur_short_sound_file_name] + [snr_value]
                                           + ["NA"] +
                                           [0] + [1] + [0] * 2 +
                                           [t0 - time_start])
                            self.apply_null_time(duration=null_time)
                        go_trial = False

                    if nogo_trial:
                        t0 = time.time()
                        response_time = self.peck_prompt(duration=max_response_time)
                        if response_time is not None:  # False alarm :(
                            self.write_csv(file_identifier,
                                           [trial_number] + ["NOGO"] + [cur_short_sound_file_name] + [snr_value] +
                                           [response_time] +
                                           [0] * 3 + [1] +
                                           [t0 - time_start])
                            # self.apply_punishment()
                            self.apply_sleep_punishment(16, wn_sound=wn_sound,
                                                        apply_wn_too=True)  # Some birds might feel "demotivated" with harsh punishment...
                        else:  # Correct rejection! :)
                            self.write_csv(file_identifier,
                                           [trial_number] + ["NOGO"] + [cur_short_sound_file_name] + [snr_value] +
                                           ["NA"] +
                                           [0] * 2 + [1] + [0] +
                                           [t0 - time_start])
                            self.apply_null_time(duration=null_time)
                        nogo_trial = False
                    trial_number += 1
                    block_index += 1
                    # Bird has to hop off the perch to reactivate switch
                    self.step_out_prompt()

                current_time = time.time() - time_start
                if current_time > duration:
                    break
            block_counter += 1

    def classical_to_operant_conditioning(self, go_sound, nogo_sound, wn_sound,
                                          classical_probability, operant_probability, iti_range=(30, 60),
                                          classical_conditioning_trial_cap=30, operant_conditioning_trial_cap=100,
                                          max_trial_duration=14400, max_response_time=None, reward_time=None,
                                          punishment_null_time=None, null_time=None, delay_time=None):
        """
        Train with classical conditioning (preexposure), test with operant conditioning
        """
        def shuffle_stimuli(trial_cap, go_probability):
            """
            This function preshuffles go/no-go stimuli order in order to assert that the number
                    of stimuli type corresponds to probability * trial_cap.
                    e.g. at 50% probability, in 100 trials, animals will get exactly 50 GOs, in pseudorandom order
            """
            go_repetitions_n = go_probability*trial_cap
            nogo_repetitions_n = trial_cap - go_repetitions_n

            rep_go_files = np.repeat('go', go_repetitions_n)
            rep_nogo_files = np.repeat('nogo', nogo_repetitions_n)

            ordered_concat = np.append(rep_go_files, rep_nogo_files)

            shuffled_indices = np.arange(0, len(ordered_concat))
            np.random.shuffle(shuffled_indices)
            return ordered_concat, shuffled_indices  # indices higher than block_size/2 are nogo

        classical_conditioning_csv_name = self.subject_paradigm_id + \
                                          '_go' + go_sound[:-4] + \
                                          '_nogo' + nogo_sound[:-4] + \
                                          '_prob' + str(classical_probability * 100) + \
                                          '_classical_conditioning'
        self.write_csv(classical_conditioning_csv_name, ["Trial_number"] + ["Trial_type"] +
                       ["Time_from_start"] + ["Stimulus"])
        operant_conditioning_csv_name = self.subject_paradigm_id + \
                                        '_go' + go_sound[:-4] + \
                                        '_nogo' + nogo_sound[:-4] + \
                                        '_prob' + str(operant_probability * 100) + \
                                        '_operant_conditioning'
        self.write_csv(operant_conditioning_csv_name, ["Trial_number"] + ["Trial_type"] + ["Response_time_s"] +
                       ["Hit"] + ["Miss"] + ["Reject"] + ["False_alarm"] + ["Time_from_start"] + ["Stimulus"])

        # Set defaults if not specified
        if go_sound is None:
            go_sound = self.GO_SOUND
        if nogo_sound is None:
            nogo_sound = self.NOGO_SOUND
        if max_response_time is None:
            max_response_time = self.RESPONSE_TIME
        if reward_time is None:
            reward_time = self.REWARD_TIME
        if punishment_null_time is None:
            punishment_null_time = self.PUNISHMENT_NULL_TIME
        if null_time is None:
            null_time = self.NULL_TIME
        if delay_time is None:
            delay_time = self.DELAY_TIME
        if wn_sound is None:
            wn_sound = self.WN_SOUND
        if iti_range is None:
            iti_range = self.ITI_RANGE

        # Flags
        go_trial = False
        nogo_trial = False

        trial_idx = 0  # Trial counter

        # I'm presorting the trial counts so that animals are exposed to EXACTLY probability * trial count
        # For example, at 50% probability, in 100 trials, animals will get exactly 50 GOs, in pseudorandom order
        classical_ordered_concat, classical_shuffled_indices = \
            shuffle_stimuli(classical_conditioning_trial_cap, classical_probability)

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        """
        This is the main classical conditioning loop
        """
        time_start = time.time()
        while trial_idx < classical_conditioning_trial_cap:  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            time.sleep(np.random.uniform(iti_range[0], iti_range[1]))
            # Choose Go or No-go song depending on the probability
            if classical_ordered_concat[classical_shuffled_indices[trial_idx]] == 'go':
                self.play_sound(go_sound)
                curr_stimulus = go_sound
                go_trial = True

            else:
                self.play_sound(nogo_sound)
                curr_stimulus = nogo_sound
                nogo_trial = True

            if go_trial:
                t0 = time.time()  # Registers current time
                self.write_csv(classical_conditioning_csv_name,
                               [trial_idx + 1] + ["GO"] +
                               [t0 - time_start] + [curr_stimulus])
                self.apply_reward(duration=reward_time)
                go_trial = False

            if nogo_trial:
                t0 = time.time()  # Registers current time
                self.write_csv(classical_conditioning_csv_name,
                               [trial_idx + 1] + ["NOGO"] +
                               [t0 - time_start] + [curr_stimulus])
                # just apply a sleep timer for the duration of the reward time
                time.sleep(reward_time)
                nogo_trial = False

            trial_idx += 1

        # Flags
        go_trial = False
        nogo_trial = False

        trial_idx = 0  # Restart trial counter

        # I'm presorting the trial counts so that animals are exposed to EXACTLY probability * trial count
        # For example, at 50% probability, in 100 trials, animals will get exactly 50 GOs, in pseudorandom order
        operant_ordered_concat, operant_shuffled_indices = \
            shuffle_stimuli(operant_conditioning_trial_cap, operant_probability)

        self.reward_off()  # just to make sure the reward is not on at the beginning of the paradigm

        """
        This is the main operant conditioning loop
        """
        curr_stimulus = ""
        operant_time_start = time.time()
        current_time = time.time() - time_start
        while (current_time <= max_trial_duration) and (
                trial_idx < operant_conditioning_trial_cap):  # "IIIIIIIIIt's TIME!"(Buffer, Bruce)
            # Birds initiate all trials!
            start_peck = self.peck_prompt(duration=(max_trial_duration - current_time))  # Birds initiate all trials!

            if start_peck is not None:
                if operant_ordered_concat[operant_shuffled_indices[trial_idx]] == 'go':
                    self.play_sound(go_sound)
                    curr_stimulus = go_sound
                    go_trial = True

                else:
                    self.play_sound(nogo_sound)
                    curr_stimulus = nogo_sound
                    nogo_trial = True

                time.sleep(delay_time)

                if go_trial:
                    t0 = time.time()  # Registers current time
                    response_time = self.peck_prompt(duration=max_response_time)
                    if response_time is not None:  # Hit! :)
                        self.write_csv(operant_conditioning_csv_name,
                                       [trial_idx + 1] + ["GO"] + [response_time] + [1] + [0] * 3 +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_reward(duration=reward_time)
                    else:  # Miss :(
                        self.write_csv(operant_conditioning_csv_name,
                                       [trial_idx + 1] + ["GO"] + ["NA"] + [0] + [1] + [0] * 2 +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_null_time(duration=null_time)
                    go_trial = False

                if nogo_trial:
                    t0 = time.time()
                    response_time = self.peck_prompt(duration=max_response_time)
                    if response_time is not None:  # False alarm :(
                        self.write_csv(operant_conditioning_csv_name,
                                       [trial_idx + 1] + ["NOGO"] + [response_time] + [0] * 3 + [1] +
                                       [t0 - time_start] + [curr_stimulus])
                        # self.apply_punishment()
                        self.apply_sleep_punishment(punishment_null_time, wn_sound=wn_sound,
                                                    apply_wn_too=True)  # Some birds might feel "demotivated" with harsh punishment...
                    else:  # Correct rejection! :)
                        self.write_csv(operant_conditioning_csv_name,
                                       [trial_idx + 1] + ["NOGO"] + ["NA"] + [0] * 2 + [1] + [0] +
                                       [t0 - time_start] + [curr_stimulus])
                        self.apply_null_time(duration=null_time)
                    nogo_trial = False
                trial_idx += 1
                # Bird has to hop off the perch to reactivate switch
                self.step_out_prompt()

            current_time = time.time() - operant_time_start


if __name__ == "__main__":
    print "THIS FILE SHOULD NOT BE RUN DIRECTLY; RUN BOOTH_DRIVER.PY INSTEAD"
