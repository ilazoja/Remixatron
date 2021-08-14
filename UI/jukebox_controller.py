import os
from pygame import mixer
import pygame.locals

from UI.gui_utils import *

SOUND_FINISHED = pygame.locals.USEREVENT + 1

class JukeboxController:

    def __init__(self, window, font, jukebox):
        self.window = window
        self.font = font

        self.initialize_controller(jukebox)

    def initialize_controller(self, jukebox):
        self.jukebox = jukebox

        # mixer.init(frequency=jukebox.sample_rate)
        self.channel = mixer.Channel(0)

        # register the event type we want fired when a sound buffer
        # finishes playing
        self.channel.set_endevent(SOUND_FINISHED)

        snd = mixer.Sound(buffer=jukebox.beats[0]['buffer'])
        self.channel.queue(snd)

        self.channel.pause()

        self.is_paused = True
        self.beat_id = 0

        self.total_indices = jukebox.beats[-1]['stop_index'] - jukebox.beats[0]['start_index']
        self.scroll_index = BAR_X
        self.selected_index = 0

        self.selected_jump_beat_num = 0
        self.selected_jump_beat_id = -1

        self.debounce = False

    def get_verbose_info(self, verbose):
        """Show statistics about the song and the analysis"""

        info = """
        filename: %s
        duration: %02d:%02d:%02d
           beats: %d
           tempo: %d bpm
        clusters: %d
        segments: %d
      samplerate: %d
        """

        (minutes, seconds) = divmod(round(self.jukebox.duration), 60)
        (hours, minutes) = divmod(minutes, 60)

        verbose_info = info % (self.jukebox.filename, hours, minutes, seconds,
                               len(self.jukebox.beats), int(round(self.jukebox.tempo)), self.jukebox.clusters, self.jukebox.segments,
                               self.jukebox.sample_rate)

        segment_map = ''
        cluster_map = ''

        segment_chars = '#-'
        cluster_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890-=,.<>/?;:!@#$%^&*()_+'

        for b in self.jukebox.beats:
            segment_map += segment_chars[b['segment'] % 2]
            cluster_map += cluster_chars[b['cluster']]

        verbose_info += "\n" + segment_map + "\n\n"

        if verbose:
            verbose_info += cluster_map + "\n\n"

        verbose_info += self.jukebox._extra_diag

        return verbose_info

    def on_sound_finished(self):

        # If on selected beat, and there is a selected jump beat, go to selected jump beat, otherwise increment by 1
        if self.selected_jump_beat_id >= 0 and self.beat_id == self.selected_beat_id:
            self.beat_id = self.selected_jump_beat_id
        else:
            self.beat_id += 1
            if self.beat_id >= len(self.jukebox.beats): # if no beats left (i.e. song finished
                self.beat_id = 0

        self.scroll_index = BAR_X + (float(self.jukebox.beats[self.beat_id]['start_index']) / float(self.total_indices)) * BAR_WIDTH
        # Channel2 sound ended, start another!

        snd = mixer.Sound(buffer=self.jukebox.beats[self.beat_id]['buffer'])
        self.channel.play(snd)

    def select_file(self):
        self.channel.pause()  # Pause before opening prompt otherwise playback will speed up
        return prompt_file()

    def open_button(self, click, mx, my):

        ## Open a new file
        open_button_box = pygame.Rect(WINDOW_WIDTH - BUTTON_WIDTH*2 - 10, 20, BUTTON_WIDTH*2, BUTTON_WIDTH)
        pygame.draw.rect(self.window, Color.GRAY.value, open_button_box)
        if open_button_box.collidepoint((mx, my)):
            if click == (1, 0, 0):
                return self.select_file()

        return None

    def write_points_to_file(self, lac_dir = ""):
        if self.selected_jump_beat_id >= 0 and self.selected_beat_id >= 0:
            start_offset = self.jukebox.beats[self.selected_jump_beat_id]['start_index']
            loop_offset = self.jukebox.beats[self.selected_beat_id]['stop_index']
            with open(os.path.join(lac_dir, "loop.txt"), "w") as output:
                output.write("\n%d " % (self.jukebox.start_index + start_offset))
                output.write("%d " % (self.jukebox.start_index + loop_offset))
                output.write(os.path.basename(self.jukebox.filename))

    def export_brstm(self):
        self.write_points_to_file(LOOPING_AUDIO_CONVERTER_DIR)
        return get_timestamp()

    def export_button(self, click, mx, my):

        if self.selected_jump_beat_id >= 0 and self.selected_beat_id >= 0:
            ## Export loop
            export_button_box = pygame.Rect(WINDOW_WIDTH - BUTTON_WIDTH*2 - 10, WINDOW_HEIGHT - BUTTON_WIDTH - 10, BUTTON_WIDTH*2, BUTTON_WIDTH)
            pygame.draw.rect(self.window, Color.FOREST_GREEN.value, export_button_box)
            if export_button_box.collidepoint((mx, my)):
                if click == (1, 0, 0):
                    return self.export_brstm()

        return None

    def play_button(self, click, mx, my):

        ## Play / pause
        play_button_box = pygame.Rect(WINDOW_WIDTH / 2 - BUTTON_WIDTH / 2, WINDOW_HEIGHT - BUTTON_WIDTH - 10, BUTTON_WIDTH, BUTTON_WIDTH)
        if play_button_box.collidepoint((mx, my)):
            if click == (1, 0, 0):
                if not self.debounce:
                    if not self.is_paused:
                        self.channel.pause()
                        self.is_paused = True
                    else:
                        self.channel.unpause()
                        self.is_paused = False
                self.debounce = True
            else:
                self.debounce = False

        pygame.draw.rect(self.window, Color.RED.value, play_button_box)

    def music_slider(self, click, mx, my, action = None):

        music_slider_bar = pygame.Rect(BAR_X, WINDOW_HEIGHT - BUTTON_WIDTH - 20 - BAR_HEIGHT - 10, BAR_WIDTH, BAR_HEIGHT)

        ## Handle mouse
        if music_slider_bar.collidepoint((mx, my)):
            if click == (1, 0, 0):
                self.scroll_index = ((mx - BAR_X) / BAR_WIDTH) * float(self.total_indices) + self.jukebox.beats[0]['start_index']
            elif click == (0, 0, 1):
                self.selected_index = ((mx - BAR_X) / BAR_WIDTH) * float(self.total_indices) + self.jukebox.beats[0]['start_index']
                self.selected_beat_id = -1
                self.selected_jump_beat_num = 0
                self.selected_jump_beat_id = -1

        pygame.draw.rect(self.window, Color.GRAY.value, music_slider_bar)

        current_jump_beat_num = 0
        current_segment = -1
        for beat in self.jukebox.beats:
            x_line = BAR_X + (float(beat['start_index']) / float(self.total_indices)) * BAR_WIDTH

            ## Adjust scroll bar so that it is at start of beat
            if self.scroll_index >= beat['start_index'] and self.scroll_index < beat['stop_index']: # find beat which index belongs to
                self.scroll_index = BAR_X + (float(beat['start_index']) / float(self.total_indices)) * BAR_WIDTH

                ## If start indices doesn't match, i.e. the scroll bar was moved, set beat id to new beat
                if beat['start_index'] != self.jukebox.beats[self.beat_id]['start_index']:
                    self.beat_id = beat['id'] - 1

            ## Draw segment borders in white
            if beat['segment'] > current_segment:
                current_segment = beat['segment']

                pygame.draw.rect(self.window, Color.WHITE.value,
                                 [x_line - SEGMENT_LINE_WIDTH/2, WINDOW_HEIGHT - BUTTON_WIDTH - 20 - BAR_HEIGHT - 20, SEGMENT_LINE_WIDTH,
                                  BAR_HEIGHT + 20])

            current_beat_color = None
            for jump_beat_id in beat['jump_candidates']:

                if jump_beat_id < beat['id']:
                    current_beat_color = Color.LIGHT_BLUE.value # Highlight beats with a earlier loop in light blue
                    if self.selected_index >= beat['start_index'] and self.selected_index < beat['stop_index']: # find beat which index belongs to
                        self.selected_beat_id = beat['id']
                        current_beat_color = Color.FIREBRICK.value # Highlight selected beat with ealier loop in red

                        x_jump_line = BAR_X + (float(self.jukebox.beats[jump_beat_id]['start_index']) / float(self.total_indices)) * BAR_WIDTH

                        # Highlight selected jump beat in green, other ones in yellow
                        jump_beat_color = Color.YELLOW.value
                        if self.selected_jump_beat_num == current_jump_beat_num:
                            self.selected_jump_beat_id = jump_beat_id
                            jump_beat_color = Color.FOREST_GREEN.value

                        pygame.draw.rect(self.window, jump_beat_color,
                                         [x_jump_line - SEGMENT_LINE_WIDTH / 2,
                                          WINDOW_HEIGHT - BUTTON_WIDTH - 20 - BAR_HEIGHT - 10, SEGMENT_LINE_WIDTH,
                                          BAR_HEIGHT])

                        current_jump_beat_num += 1

                if current_beat_color:
                    pygame.draw.rect(self.window, current_beat_color,
                             [x_line - SEGMENT_LINE_WIDTH / 2,
                              WINDOW_HEIGHT - BUTTON_WIDTH - 20 - BAR_HEIGHT - 10, SEGMENT_LINE_WIDTH,
                              BAR_HEIGHT])


        pygame.draw.rect(self.window, Color.BLACK.value, [self.scroll_index - SCROLL_WIDTH / 2, WINDOW_HEIGHT - BUTTON_WIDTH - 20 - BAR_HEIGHT - 20, SCROLL_WIDTH, BAR_HEIGHT + 20])


        # TODO: Right click, highlight a beat (maybe closest beat to the left) in red and beats to transition to in yellow, select beats using keypad, scrollwheel or arrow keys

        # TODO: Display audio signal?

        # TODO: Export loop, automatically convert using LoopingAudioConverter

        # TODO: Select songs

        # TODO: Volume slider at bottom left