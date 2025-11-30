# Ambulance Logistics App - Kharkiv

Desktop application for ambulance logistics simulation in Kharkiv.

## Features

- Modern dark UI (Discord/Spotify style)
- Interactive Kharkiv city map
- 6 strategically placed ambulance stations
- Emergency call generation
- Real-time ambulance status display
- Fast and responsive (instant map updates)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Click "Generate Emergency" to simulate emergency calls. Only one emergency at a time (new one replaces previous).

## Project Structure

- `main.py` - Main PyQt6 application
- `map_generator.py` - Folium map generation
- `map.html` - Generated map file (auto-created)
