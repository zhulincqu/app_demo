push_button_style =\
"""
QPushButton {
    border: 2px solid #8f8f91;
    border-radius: 6px;
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #f6f7fa, stop: 1 #dadbde);
    min-width: 80px;
    min-height: 30px;
}
QPushButton:pressed {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                    stop: 0 #dadbde, stop: 1 #f6f7fa);
}
"""

label_style = \
"""
QLabel {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10pt;
    padding: 2px;
}
"""

spin_box_style = \
"""
QDoubleSpinBox {
    min-width: 120px;
    min-height: 30px;
    padding-right: 4px; /* make room for the arrows */
    border-width: 2;
}
"""


