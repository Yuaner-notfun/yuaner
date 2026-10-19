import mido
import os
import time
import ctypes
from ctypes import wintypes

# 21-key instrument notes used by WWM (three octaves of natural notes).
INSTRUMENT_NOTES_21 = [
    48, 50, 52, 53, 55, 57, 59,
    60, 62, 64, 65, 67, 69, 71,
    72, 74, 76, 77, 79, 81, 83,
]
INSTRUMENT_KEYS_21 = [
    'z', 'x', 'c', 'v', 'b', 'n', 'm',
    'a', 's', 'd', 'f', 'g', 'h', 'j',
    'q', 'w', 'e', 'r', 't', 'y', 'u',
]
KEY_MAP = dict(zip(INSTRUMENT_NOTES_21, INSTRUMENT_KEYS_21))

# 36-key mode mapping from the WWM keyboard image.
# Each row is chromatic from left to right; MIDI note order is 48..83 from
# Low→Middle→High. These are physical keys, so no Shift/Ctrl modifier is used.
KEY_MAP_36 = {
    48: 'z', 49: '3', 50: 'x', 51: '6', 52: 'c', 53: 'v',
    54: '9', 55: 'b', 56: '=', 57: 'n', 58: '/', 59: 'm',
    60: 'a', 61: '2', 62: 's', 63: '5', 64: 'd', 65: 'f',
    66: '8', 67: 'g', 68: '-', 69: 'h', 70: '.', 71: 'j',
    72: 'q', 73: '1', 74: 'w', 75: '4', 76: 'e', 77: 'r',
    78: '7', 79: 't', 80: '0', 81: 'y', 82: ',', 83: 'u'
}

# 36-key canvas rows exactly matching the attached screenshot, with High first
# as the visual row order and Low last, preserving the same 12-key shape.
KEY_ROWS_36 = {
    'High': ['q', '1', 'w', '4', 'e', 'r', '7', 't', '0', 'y', ',', 'u'],
    'Middle': ['a', '2', 's', '5', 'd', 'f', '8', 'g', '-', 'h', '.', 'j'],
    'Low': ['z', '3', 'x', '6', 'c', 'v', '9', 'b', '=', 'n', '/', 'm']
}

# 50-key chromatic layout from the game's full keyboard configuration.
# It contains four complete chromatic octaves plus C and C# of the next one.
# The first key ("1" with two dots below in the game) is MIDI C2 = 36.
KEYS_50 = [
    # C2-B2: numpad group
    'NUMPADMULTIPLY', 'NUMPADDIVIDE', 'NUMPAD9', 'NUMPAD8',
    'NUMPAD7', 'NUMPAD5', 'NUMPAD6', 'NUMPAD3',
    'NUMPAD4', 'NUMPAD1', 'NUMPAD2', '/',
    # C3-B3: punctuation/number group
    '`', ',', ';', "'", '[', ']', '\\', '5', '=', '0', '-', '9',
    # C4-B4: Z-M group
    'z', 's', 'x', 'd', 'c', 'v', 'g', 'b', 'h', 'n', 'j', 'm',
    # C5-B5: W-I group
    'w', '3', 'e', '4', 'r', 't', '6', 'y', '7', 'u', '8', 'i',
    # C6-C#6: final two keys
    '1', '2',
]
KEY_MAP_50 = dict(enumerate(KEYS_50, start=36))

SCALES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

# Convert a visual key symbol into a Windows virtual-key code.
# This is critical for punctuation rows such as [, ], /, ;, , and .
# because ord(key.upper()) produces the character code, not the keyboard scan
# layout code that SendInput/MapVirtualKeyW needs for the active game window.
def key_to_vk(key):
    key = str(key)
    upper = key.upper()

    numpad_map = {
        'NUMPAD0': 0x60, 'NUMPAD1': 0x61, 'NUMPAD2': 0x62,
        'NUMPAD3': 0x63, 'NUMPAD4': 0x64, 'NUMPAD5': 0x65,
        'NUMPAD6': 0x66, 'NUMPAD7': 0x67, 'NUMPAD8': 0x68,
        'NUMPAD9': 0x69, 'NUMPADMULTIPLY': 0x6A,
        'NUMPADADD': 0x6B, 'NUMPADSUBTRACT': 0x6D,
        'NUMPADDECIMAL': 0x6E, 'NUMPADDIVIDE': 0x6F,
    }
    if upper in numpad_map:
        return numpad_map[upper]

    # Letter and number keys.
    if 'A' <= upper <= 'Z':
        return ord(upper)
    if '0' <= key <= '9':
        return ord(key)

    # Common punctuation map keyed to the screenshot's 36-key row.
    punct_map = {
        '`': 0xC0, '~': 0xC0,
        '1': 0x31, '!': 0x31,
        '2': 0x32, '@': 0x32,
        '3': 0x33, '#': 0x33,
        '4': 0x34, '$': 0x34,
        '5': 0x35, '%': 0x35,
        '6': 0x36, '^': 0x36,
        '7': 0x37, '&': 0x37,
        '8': 0x38, '*': 0x38,
        '9': 0x39, '(': 0x39,
        '0': 0x30, ')': 0x30,
        '-': 0xBD, '_': 0xBD,
        '=': 0xBB, '+': 0xBB,
        '[': 0xDB, '{': 0xDB,
        ']': 0xDD, '}': 0xDD,
        '\\': 0xDC, '|': 0xDC,
        ';': 0xBA, ':': 0xBA,
        "'": 0xDE, '"': 0xDE,
        ',': 0xBC, '<': 0xBC,
        '.': 0xBE, '>': 0xBE,
        '/': 0xBF, '?': 0xBF,
    }

    if key in punct_map:
        return punct_map[key]

    # Fallback to `ord` for any safe ASCII character.
    return ord(key.upper()) if key else 0


def parse_key(key):
    """Return ``(base_key, modifier_vk)`` for a WWM key expression."""
    key = str(key).lower()
    if key.startswith('shift+'):
        return key[6:], 0x10  # VK_SHIFT
    if key.startswith('ctrl+'):
        return key[5:], 0x11  # VK_CONTROL
    return key, None


def normalize_into_range(note, low=48, high=83):
    """Fold a MIDI note into WWM's playable 21-key range."""
    target = int(note)
    while target < low:
        target += 12
    while target > high:
        target -= 12
    return target


def closest_instrument_note(note):
    """Return the closest natural instrument note after normalization."""
    target = normalize_into_range(note)
    return min(INSTRUMENT_NOTES_21, key=lambda candidate: abs(candidate - target))

# Scan midi file in mid_repo folder
def midScanner():
    m_file = os.listdir("."+os.sep+"midi_repo")
    ret = []
    for i in m_file:
        if os.path.splitext(i)[1] == '.mid':
            ret.append(i)
    return ret

# Translate midi note to keyboard
def noteTrans(m_note_value, use_36_keys=False, use_50_keys=False):
    if use_50_keys:
        target = normalize_into_range(m_note_value, 36, 85)
        return nearest_key_from_map(target, KEY_MAP_50)
    if use_36_keys:
        target = normalize_into_range(m_note_value)
        return nearest_key_from_map(target, KEY_MAP_36)
    return KEY_MAP[closest_instrument_note(m_note_value)]


def nearest_key_from_map(note, key_map):
    """Return the key whose MIDI note is closest to ``note``."""
    if not key_map:
        return None
    nearest_note = min(key_map, key=lambda candidate: abs(candidate - int(note)))
    return key_map[nearest_note]

# Check if note is in range
def isNoteInRange(note, use_36_keys=False, use_50_keys=False):
    if use_50_keys:
        return True
    if use_36_keys:
        return True
    # 21-key mode normalizes every MIDI note into the playable range.
    return True

# Helper to choose active map
def get_active_key_map(use_36_keys=False, use_50_keys=False):
    if use_50_keys:
        return KEY_MAP_50
    return KEY_MAP_36 if use_36_keys else KEY_MAP

# Player only support melody in C Major, Use this to translate other scale to C Major
# In 36-key screenshot mode the map is the visible 3-row layout itself, so the
# transposition candidate list must not invent a conceptual shift that bends the
# piano note sequence into a different row. We keep it anchored to 0.
def allToCMajor(m_file_name, use_36_keys=False):
    # Both layouts use an identity transposition. In 21-key mode WWM's
    # mapper normalizes every source note; 36-key mode is a fixed image map.
    return [0]

# Auto-adjust to best key when out of range
# In the 36-key screenshot mode the intended layout is a fixed visual keyboard
# with three rows. It must not invent a transposition shift for the MIDI source
# because that creates the false pitch-lag heard when comparing against the
# original piano MIDI file.
def findBestKey(m_file_name, use_36_keys=False):
    """Return identity because WWM normalizes notes during mapping."""
    return 0

# Check out of range notes
def getOutOfRangeNotes(m_file_name, m_key_add, use_36_keys=False, use_50_keys=False):
    if use_36_keys or use_50_keys:
        return []

    file_name = "." + os.sep + "midi_repo" + os.sep + m_file_name
    out_of_range = []
    key_map = get_active_key_map(use_36_keys)
    
    try:
        for msg in mido.MidiFile(file_name):
            if msg.type == "note_on":
                note = int(msg.note) + m_key_add
                if use_36_keys and note not in key_map:
                    out_of_range.append(note)
    except Exception as e:
        print(f"Error checking range: {e}")
    
    return list(set(out_of_range))

# Get total MIDI duration
def getMidiDuration(m_file_name):
    file_name = "." + os.sep + "midi_repo" + os.sep + m_file_name
    try:
        midi = mido.MidiFile(file_name)
        return midi.length
    except:
        return 0

# SendInput related definitions
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


class MidiPlayer:
    """Enhanced MIDI player with pause/resume and real-time BPM control"""
    
    def __init__(self, file_name, bpm, key_add, allow_out_range=False,
                 use_36_keys=False, use_50_keys=False):
        self.file_name = "." + os.sep + "midi_repo" + os.sep + file_name
        self.bpm = bpm
        self.key_add = key_add
        self.allow_out_range = allow_out_range
        self.use_36_keys = use_36_keys
        self.use_50_keys = use_50_keys
        self.is_paused = False
        self.should_stop = False
        # Reference counts allow overlapping notes/chords that map to the
        # same physical key without releasing it too early.
        self.pressed_keys = {}
        self.current_time = 0
        self.total_time = 0
        
        # Windows API setup
        self.SendInput = ctypes.windll.user32.SendInput
        self.MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
        
        # Load MIDI
        try:
            self.midi = mido.MidiFile(self.file_name)
            self.total_time = self.midi.length
        except Exception as e:
            raise Exception(f"Failed to load MIDI: {e}")
    
    def send_key(self, key, is_press):
        """Send keyboard input using SendInput"""
        if key is None:
            return

        base_key, modifier_vk = parse_key(key)

        def emit(vk_code, pressed):
            scan_code = self.MapVirtualKey(vk_code, 0)
            extra = ctypes.c_ulong(0)
            ii_ = Input_I()
            flags = 0 if pressed else 0x0002
            ii_.ki = KeyBdInput(vk_code, scan_code, flags, 0, ctypes.pointer(extra))
            event = Input(ctypes.c_ulong(1), ii_)
            self.SendInput(1, ctypes.pointer(event), ctypes.sizeof(event))

        vk_code = key_to_vk(base_key)
        if modifier_vk is not None:
            # The game expects modifier and note to be sent as one immediate
            # combo; release in reverse order so no modifier remains stuck.
            if is_press:
                emit(modifier_vk, True)
                emit(vk_code, True)
            else:
                emit(vk_code, False)
                emit(modifier_vk, False)
        else:
            emit(vk_code, is_press)
    
    def pause(self):
        """Pause playback"""
        self.is_paused = True
    
    def resume(self):
        """Resume playback"""
        self.is_paused = False
    
    def stop(self):
        """Stop playback"""
        self.should_stop = True
        # Release all pressed keys
        for key in list(self.pressed_keys):
            self.send_key(key, False)
        self.pressed_keys.clear()
    
    def set_bpm(self, new_bpm):
        """Change BPM in real-time"""
        self.bpm = max(40, min(2000, new_bpm))
    
    def play(self, progress_callback=None, note_callback=None):
        """Play MIDI with callbacks for progress and note visualization."""
        real_time = float(120 / self.bpm)

        for msg in self.midi:
            # Check for stop
            if self.should_stop:
                break

            # Handle pause
            while self.is_paused and not self.should_stop:
                time.sleep(0.01)

            # Update BPM dynamically
            real_time = float(120 / self.bpm)

            # Handle timing
            if msg.time > 0:
                time.sleep(float(msg.time) * real_time)
                self.current_time += msg.time

                if progress_callback:
                    progress_callback(self.current_time, self.total_time)

            # Keep the key held until note_off, matching the original project
            # and the game's expected keyboard input behavior.
            if msg.type == "note_on" and msg.velocity > 0:
                note = int(msg.note) + self.key_add
                key = noteTrans(note, self.use_36_keys, self.use_50_keys)
                if key:
                    if self.pressed_keys.get(key, 0) == 0:
                        self.send_key(key, True)
                    self.pressed_keys[key] = self.pressed_keys.get(key, 0) + 1

                    if note_callback:
                        note_callback(key)

            elif (
                msg.type == "note_off"
                or (msg.type == "note_on" and msg.velocity == 0)
            ):
                note = int(msg.note) + self.key_add
                key = noteTrans(note, self.use_36_keys, self.use_50_keys)
                if key and key in self.pressed_keys:
                    self.pressed_keys[key] -= 1
                    if self.pressed_keys[key] <= 0:
                        self.send_key(key, False)
                        del self.pressed_keys[key]

        # Release any remaining keys from the old hold model if present.
        for key in list(self.pressed_keys):
            self.send_key(key, False)
        self.pressed_keys.clear()


def counter(m_second):
    """Countdown timer"""
    for i in range(m_second):
        time.sleep(1)