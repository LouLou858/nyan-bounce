#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nyan_bounce.py
Nyan Cat qui rebondit sur le bureau avec musique, traînée persistante.
- Place nyan.gif et nyan.mp3 (ou nyan.ogg) dans le dossier 'assets'
- Touche N : pause / reprise (toggle)
- Clic droit ou Esc : quitter
- Si la traînée couvre trop l'écran -> arrêt automatique
Dépendances: PyQt5, pygame
"""

import sys
import os
import math
from PyQt5.QtCore import Qt, QTimer, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QMovie

# --- Config (modifie si besoin) ---
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
MUSIC_FILE = os.path.join(ASSETS_DIR, "nyan.mp3")  # change si besoin (nyan.ogg, nyan.wav)
GIF_FILE = os.path.join(ASSETS_DIR, "nyan.gif")

# comportement
TIMER_MS = 16            # ~60 FPS
SPEED = 6.5              # vitesse initiale (pixels / tick)
BOUNCE_DAMPING = 1.0     # 1.0 = rebond complet (pas d'absorption)
TRAIL_FADE = False       # si True on ajoute légère transparence à la traînée au fil du temps
SATURATION_CHECK_INTERVAL_MS = 1000  # intervalle pour vérifier saturation
SATURATION_THRESHOLD = 0.60  # proportion d'écran couverte (0.6 => 60%) avant arrêt
TRAIL_BRUSH_WIDTH = 38   # largeur de la traînée (px)
PERSISTENT_TRAIL = True  # la traînée reste (true)
# ----------------------------------

if not os.path.exists(GIF_FILE):
    print(f"AVERTISSEMENT : '{GIF_FILE}' introuvable dans {ASSETS_DIR}. Place un GIF nommé 'nyan.gif'.")
if not os.path.exists(MUSIC_FILE):
    print(f"AVERTISSEMENT : '{MUSIC_FILE}' introuvable dans {ASSETS_DIR}. Place un fichier audio nommé 'nyan.mp3'.")

try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except Exception as e:
    print("Impossible d'initialiser pygame.mixer (son non disponible).", e)
    PYGAME_OK = False

class NyanWindow(QWidget):
    def __init__(self):
        super().__init__()

        # fenêtre fullscreen transparente
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.showFullScreen()

        screen_geo = QApplication.primaryScreen().geometry()
        self.screen_w = screen_geo.width()
        self.screen_h = screen_geo.height()

        # buffer pour traînée persistante (avec alpha)
        self.buffer = QPixmap(self.screen_w, self.screen_h)
        self.buffer.fill(Qt.transparent)

        # chargement GIF (QMovie pour accéder aux frames)
        self.movie = None
        self.frame_pix = None
        if os.path.exists(GIF_FILE):
            try:
                self.movie = QMovie(GIF_FILE)
                self.movie.start()
                frame_size = self.movie.currentPixmap().size()
                max_dim = int(min(self.screen_w, self.screen_h) * 0.20)
                if max(frame_size.width(), frame_size.height()) > max_dim:
                    self.movie.setScaledSize(QSize(max_dim, int(frame_size.height() * max_dim/frame_size.width())))
            except Exception as e:
                print("Erreur chargement GIF:", e)
                self.movie = None

        self.nyan_w = self.movie.currentPixmap().width() if self.movie else 128
        self.nyan_h = self.movie.currentPixmap().height() if self.movie else 64
        self.x = (self.screen_w - self.nyan_w) // 2
        self.y = (self.screen_h - self.nyan_h) // 3
        self.vx = SPEED
        self.vy = SPEED * 0.6

        self.paused = False
        self.running = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(TIMER_MS)

        self.sat_timer = QTimer()
        self.sat_timer.timeout.connect(self.check_saturation)
        self.sat_timer.start(SATURATION_CHECK_INTERVAL_MS)

        if PYGAME_OK and os.path.exists(MUSIC_FILE):
            try:
                pygame.mixer.music.load(MUSIC_FILE)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print("Erreur lecture musique:", e)

        self.last_drawn_pos = None
        self.show()

    def tick(self):
        if not self.running:
            return
        if self.paused:
            return

        if self.movie:
            self.frame_pix = self.movie.currentPixmap()
            if self.frame_pix.isNull():
                self.frame_pix = None
            self.nyan_w = self.movie.currentPixmap().width()
            self.nyan_h = self.movie.currentPixmap().height()

        self.x += self.vx
        self.y += self.vy

        if self.x <= 0:
            self.x = 0
            self.vx = abs(self.vx) * BOUNCE_DAMPING
        if self.x + self.nyan_w >= self.screen_w:
            self.x = self.screen_w - self.nyan_w
            self.vx = -abs(self.vx) * BOUNCE_DAMPING
        if self.y <= 0:
            self.y = 0
            self.vy = abs(self.vy) * BOUNCE_DAMPING
        if self.y + self.nyan_h >= self.screen_h:
            self.y = self.screen_h - self.nyan_h
            self.vy = -abs(self.vy) * BOUNCE_DAMPING

        self.draw_trail_segment(int(self.x + self.nyan_w/2), int(self.y + self.nyan_h/2))
        self.update()

    def draw_trail_segment(self, cx, cy):
        painter = QPainter(self.buffer)
        painter.setRenderHint(QPainter.Antialiasing)
        w = TRAIL_BRUSH_WIDTH
        h = int(w * 0.5)
        offset_x = -int(self.nyan_w * 0.6) if self.vx >= 0 else int(self.nyan_w * 0.6)
        base_x = cx + offset_x
        base_y = cy
        colors_hues = [0, 30, 60, 120, 210, 260, 290]
        for i, hue in enumerate(colors_hues):
            alpha = 200
            if TRAIL_FADE:
                alpha = max(40, alpha - i * 12)
            color = QColor.fromHsv(hue % 360, 220, 255, alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            band_w = int(w * (1 - i * 0.06))
            band_h = h
            rx = base_x - i * int(w * 0.55)
            ry = base_y - band_h // 2
            rect = QRectF(rx - band_w, ry, band_w * 2, band_h)
            painter.drawRoundedRect(rect, band_h/2, band_h/2)
        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, self.buffer)
        if self.frame_pix and not self.frame_pix.isNull():
            painter.drawPixmap(int(self.x), int(self.y), self.frame_pix)
        else:
            painter.setBrush(QColor(255, 200, 200, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(self.x), int(self.y), 120, 60)
        painter.end()

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key_N:
            self.toggle_pause()
        elif k == Qt.Key_Escape:
            self.quit_clean()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.quit_clean()
        else:
            super().mousePressEvent(event)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            print("PAUSE activée (touche N) : mouvement et musique en pause.")
            if PYGAME_OK:
                pygame.mixer.music.pause()
        else:
            print("Reprise (touche N).")
            if PYGAME_OK:
                pygame.mixer.music.unpause()

    def check_saturation(self):
        if not PERSISTENT_TRAIL:
            return
        img: QImage = self.buffer.toImage()
        sample_w = 200
        sample_h = max(1, int(sample_w * self.screen_h / max(1, self.screen_w)))
        tiny = img.scaled(sample_w, sample_h, transformMode=Qt.SmoothTransformation)
        opaque = 0
        total = sample_w * sample_h
        for y in range(sample_h):
            for x in range(sample_w):
                a = QColor(tiny.pixel(x, y)).alpha()
                if a > 10:
                    opaque += 1
        prop = opaque / total
        if prop >= SATURATION_THRESHOLD:
            print(f"Écran saturé ({prop:.2%}), arrêt automatique.")
            self.quit_clean()

    def quit_clean(self):
        self.running = False
        self.timer.stop()