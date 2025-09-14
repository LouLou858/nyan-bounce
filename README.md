# nyan-bounce

Nyan Cat bouncing around the desktop with music and a persistent trail — a harmless and voluntary project.

**Features**
- Transparent window always on top
- Nyan Cat bounces everywhere
- Background music (loop)
- `N` key: pause/resume (toggle)
- Right click or `Esc`: quit
- Persistent trail drawn
- Automatic shutdown control if the trail covers too much of the screen (saturation)

> **Important**: This program must be launched voluntarily by the user. It does not modify the system, does not install itself at startup, and is not malware.

## Prerequisites
- Python 3.8+
- pip

## Install
```bash
# (optional) create a venv
python -m venv venv
source venv/bin/activate  # mac/linux
venv\Scripts\activate     # windows

pip install -r requirements.txt

Translated with DeepL.com (free version)