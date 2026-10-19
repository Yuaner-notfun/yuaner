"""
Thread classes for MIDI playback
"""
from PyQt5.QtCore import QThread, pyqtSignal
import Player as GZP
import win32gui


def list_visible_windows(excluded_hwnd=None):
    """Return titled, visible top-level windows as (handle, title) pairs."""
    windows = []
    def collect(hwnd, _):
        if (hwnd != excluded_hwnd and win32gui.IsWindowVisible(hwnd)
                and not win32gui.IsIconic(hwnd)):
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                windows.append((hwnd, title))

    win32gui.EnumWindows(collect, None)
    return windows


class PlaybackThread(QThread):
    """Background thread for MIDI playback"""
    progress_signal = pyqtSignal(float, float)
    finished_signal = pyqtSignal()
    note_played_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, file_name, keyadd, bpm, allow_out_range,
                 use_36_keys=False, use_50_keys=False, target_hwnd=None):
        super().__init__()
        self.file_name = file_name
        self.keyadd = keyadd
        self.bpm = bpm
        self.allow_out_range = allow_out_range
        self.use_36_keys = use_36_keys
        self.use_50_keys = use_50_keys
        self.target_hwnd = target_hwnd
        self.player = None
        
    def run(self):
        try:
            hwnd = self.target_hwnd
            if (not hwnd or not win32gui.IsWindow(hwnd)
                    or not win32gui.IsWindowVisible(hwnd)
                    or win32gui.IsIconic(hwnd)):
                raise RuntimeError(
                    "Cửa sổ target không còn hiển thị. "
                    "Hãy làm mới danh sách và chọn lại cửa sổ."
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