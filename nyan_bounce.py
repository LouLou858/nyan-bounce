#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nyan_bounce.py
Nyan Cat rebondit sur le bureau avec une traînée arc-en-ciel propre.
"""

import sys, os, math, random
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget

# --- CONFIG ---
GIF_FILE = os.path.join("assets", "nyan_cat.png")  # sprite fixe du Nyan Cat
NYAN_SIZE = 96
SPEED = 4
TRAIL_LENGTH = 20
TRAIL_BLOCK = 12  # taille des rectangles
RAINBOW = [
    QColor(255, 0, 0),    # Rouge
    QColor(255, 127, 0),  # Orange
    QColor(255, 255, 0),  # Jaune
    QColor(0, 255, 0),    # Vert
    QColor(0, 0, 255),    # Bleu
    QColor(139, 0, 255)   # Violet
]

class NyanBounce(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Charger sprite
        self.nyan = QPixmap(GIF_FILE).scaled(NYAN_SIZE, NYAN_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Position / vitesse
        screen = QApplication.primaryScreen().geometry()
        self.x, self.y = screen.width()//3, screen.height()//3
        self.vx, self.vy = SPEED, SPEED

        # Liste des positions passées
        self.trail = []

        # Timer animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)

        self.resize(screen.width(), screen.height())
        self.show()

    def update_frame(self):
        screen = QApplication.primaryScreen().geometry()

        # Màj position
        self.x += self.vx
        self.y += self.vy

        # Rebonds
        if self.x <= 0 or self.x + NYAN_SIZE >= screen.width():
            self.vx = -self.vx
        if self.y <= 0 or self.y + NYAN_SIZE >= screen.height():
            self.vy = -self.vy

        # Ajouter à la trail
        self.trail.append((self.x, self.y, self.vx, self.vy))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dessiner trail bloc par bloc
        for i, (tx, ty, vx, vy) in enumerate(self.trail):
            angle = math.atan2(vy, vx)
            for j, color in enumerate(RAINBOW):
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                dx = -math.cos(angle) * (j * TRAIL_BLOCK)
                dy = -math.sin(angle) * (j * TRAIL_BLOCK)
                rect = QRectF(tx + NYAN_SIZE/2 + dx,
                              ty + NYAN_SIZE/2 + dy,
                              TRAIL_BLOCK, TRAIL_BLOCK)
                painter.drawRect(rect)

        # Dessiner Nyan Cat
        painter.drawPixmap(self.x, self.y, self.nyan)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NyanBounce()
    sys.exit(app.exec_())
