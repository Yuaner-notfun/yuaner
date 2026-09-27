"""
Thread classes for MIDI playback
"""
from PyQt5.QtCore import QThread, pyqtSignal
import Player as GZP
import win32gui


GAME_WINDOW_TITLES = (
    "SWORDOFJUSTICE",
    "逆水寒手游桌面版",
)


def find_game_window():
    """Find the game window using the current and legacy window titles."""
    # Fast path for known exact titles.
    for title in GAME_WINDOW_TITLES:
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            return hwnd

    # Fallback for capitalization or a title suffix/prefix added by the game.
    matches = []

    def collect(hwnd, _):
        title = win32gui.GetWindowText(hwnd).strip().casefold()
        if title and any(candidate.casefold() in title for candidate in GAME_WINDOW_TITLES):
            matches.append(hwnd)

    win32gui.EnumWindows(collect, None)
    return matches[0] if matches else None


class PlaybackThread(QThread):
    """Background thread for MIDI playback"""
    progress_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()
    note_played_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, file_name, keyadd, bpm, allow_out_range,
                 use_36_keys=False, use_50_keys=False):
        super().__init__()
        self.file_name = file_name
        self.keyadd = keyadd
        self.bpm = bpm
        self.allow_out_range = allow_out_range
        self.use_36_keys = use_36_keys
        self.use_50_keys = use_50_keys
        self.player = None
        
    def run(self):
        try:
            # Activate game window
            hwnd = find_game_window()
            if not hwnd:
                raise RuntimeError(
                    "Không tìm thấy cửa sổ game 'SWORDOFJUSTICE' "
                    "hoặc '逆水寒手游桌面版'. "
                    "Hãy mở game trước khi phát MIDI."
                )

            win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
            
            # Create player instance
            self.player = GZP.MidiPlayer(
                self.file_name,
                self.bpm,
                self.keyadd,
                self.allow_out_range,
                self.use_36_keys,
                self.use_50_keys
            )
            
            # Play with callbacks
            self.player.play(
                progress_callback=self.progress_signal.emit,
                note_callback=self.note_played_signal.emit
            )
            
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def pause(self):
        if self.player:
            self.player.pause()
    
    def resume(self):
        if self.player:
            self.player.resume()
    
    def stop(self):
        if self.player:
            self.player.stop()
        self.terminate()
    
    def set_bpm(self, new_bpm):
        if self.player:
            self.player.set_bpm(new_bpm)