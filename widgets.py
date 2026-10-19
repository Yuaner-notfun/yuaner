
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QFont

try:
    from Player import KEY_ROWS_36, KEYS_50
except Exception:
    KEY_ROWS_36 = {
        'High': ['q', '1', 'w', '4', 'e', 'r', '7', 't', ',', 'y', ';', 'u'],
        'Middle': ['a', '2', 's', '5', 'd', 'f', '8', 'g', '.', 'h', '.', 'j'],
        'Low': ['z', '3', 'x', '6', 'c', 'v', '9', 'b', '/', 'n', '[', 'm']
    }
    KEYS_50 = []


class NoteVisualization(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_notes = set()

        # 36-key screenshot layout: High / Middle / Low on three rows.
        # The row order and the key labels are now pulled from the same map
        # source as the MIDI translator so the UI and note engine stay aligned.
        self.note_rows = [
            {'label': 'High', 'keys': [k.upper() for k in KEY_ROWS_36['High']]},
            {'label': 'Middle', 'keys': [k.upper() for k in KEY_ROWS_36['Middle']]},
            {'label': 'Low', 'keys': [k.upper() for k in KEY_ROWS_36['Low']]}
        ]
        
        self.setMinimumHeight(180)
        self.setMaximumHeight(220)
        
        # Timer to fade out notes
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_notes)
        self.fade_timer.start(100)

    def set_key_mode(self, use_50_keys=False):
        """Switch the visual keyboard to the selected key layout."""
        if use_50_keys:
            self.note_rows = [
                {'label': '1', 'keys': [k.upper() for k in KEYS_50[0:12]]},
                {'label': '2', 'keys': [k.upper() for k in KEYS_50[12:24]]},
                {'label': '3', 'keys': [k.upper() for k in KEYS_50[24:36]]},
                {'label': '4', 'keys': [k.upper() for k in KEYS_50[36:48]]},
                {'label': '5', 'keys': [k.upper() for k in KEYS_50[48:50]]},
            ]
        else:
            self.note_rows = [
                {'label': 'High', 'keys': [k.upper() for k in KEY_ROWS_36['High']]},
                {'label': 'Middle', 'keys': [k.upper() for k in KEY_ROWS_36['Middle']]},
                {'label': 'Low', 'keys': [k.upper() for k in KEY_ROWS_36['Low']]},
            ]
        self.update()
    
    def add_note(self, key):
        self.active_notes.add(key.upper())
        self.update()
        
        # Auto-remove after 500ms
        QTimer.singleShot(500, lambda: self.remove_note(key))
    
    def remove_note(self, key):
        self.active_notes.discard(key.upper())
        self.update()
    
    def fade_notes(self):
        if self.active_notes:
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Check dark mode
        dark_mode = False
        if self.parent() and hasattr(self.parent(), 'dark_mode'):
            dark_mode = self.parent().dark_mode
        
        bg_color = QColor(20, 20, 25) if dark_mode else QColor(230, 235, 240)
        painter.fillRect(self.rect(), bg_color)
        
        max_keys_per_row = 12
        key_size = min((width - 80) / max_keys_per_row, 34)
        row_height = (height - 40) / max(len(self.note_rows), 1)
        
        font = QFont("Arial", 11, QFont.Bold)
        painter.setFont(font)
        
        for row_index, row_data in enumerate(self.note_rows):
            row_label = row_data['label']
            row_keys = row_data['keys']
            num_keys = len(row_keys)
            
            painter.setPen(QColor(180, 220, 250) if dark_mode else QColor(40, 90, 120))
            painter.drawText(10, int(18 + row_index * row_height), row_label)
            
            total_width = num_keys * key_size
            start_x = 60 + (width - 80 - total_width) / 2
            start_y = 14 + (row_index * row_height) + (row_height - key_size) / 2
            
            for i, key in enumerate(row_keys):
                x = start_x + (i * key_size)
                
                if key.upper() in self.active_notes:
                    fill_color = QColor(100, 200, 255, 220)
                    border_color = QColor(150, 220, 255)
                    glow = True
                else:
                    if dark_mode:
                        fill_color = QColor(50, 55, 65, 150)
                        border_color = QColor(80, 85, 95)
                    else:
                        fill_color = QColor(200, 205, 215, 180)
                        border_color = QColor(150, 155, 165)
                    glow = False
                
                if glow:
                    glow_color = QColor(100, 200, 255, 80)
                    painter.setBrush(glow_color)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(int(x + key_size / 2 - key_size * 0.55),
                                        int(start_y - key_size * 0.04),
                                        int(key_size * 1.1),
                                        int(key_size * 1.1))
                
                painter.setBrush(fill_color)
                painter.setPen(border_color)
                painter.drawRoundedRect(int(x), int(start_y), int(key_size), int(key_size * 0.8), 4, 4)
                
                if key.upper() in self.active_notes:
                    text_color = QColor(255, 255, 255)
                else:
                    text_color = QColor(180, 180, 180) if dark_mode else QColor(100, 100, 100)
                
                painter.setPen(text_color)
                painter.drawText(int(x), int(start_y), int(key_size), int(key_size * 0.8), Qt.AlignCenter, f"[{key}]")