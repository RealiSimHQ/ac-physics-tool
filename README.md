# AiO Drift Physics Swapper

**Live Site:** https://realisimhq.github.io/ac-physics-tool/

A client-side web application for swapping Assetto Corsa car physics with professional drift carpacks.

## Features

- 🎯 **Auto-Matching**: Automatically finds the best donor car based on weight, wheelbase, and track width
- 📦 **6 Carpacks**: BDC, DWG, Gravy Garage, NNTS, Swarm, WDTS (62 total donor cars)
- 🌙 **Dark Racing Aesthetic**: Polished UI with cyan/neon accents
- 📱 **Mobile Responsive**: Works on desktop and mobile devices
- 🔒 **Client-Side Only**: All processing happens in your browser (no data uploaded to servers)
- ⚡ **Instant Download**: Get your `data_<packname>.zip` immediately

## How to Use

1. **Upload** your car's `data/` folder (drag-and-drop or click to browse)
2. **Select** a carpack from the available options
3. **Download** the matched physics swap as a ZIP file

## What Gets Swapped

### Preserved from Original Car
- Car name, mass, inertia
- Wheelbase, track width, tire radius
- Suspension geometry (wishbone points)
- Graphics offsets

### Taken from Donor Carpack
- Engine, drivetrain, brakes, electronics
- Tire compounds and characteristics
- Aero, setup options, damage model
- All lookup tables (.lut files)

### Never Included
- Visual files (colliders, lods, lights, sounds, etc.)
- AI files
- Camera files

## Technical Details

- **Stack**: Pure HTML/CSS/JavaScript (no build process)
- **Libraries**: JSZip for ZIP generation
- **Hosting**: GitHub Pages
- **Data**: All carpack physics pre-bundled as JSON

## Carpacks Included

| Pack | Cars | Description |
|------|------|-------------|
| BDC | 10 | StreetSpec series (extended-2 physics) |
| DWG | 6 | Drift Works Garage |
| Gravy Garage | 7 | Community favorites |
| NNTS | 6 | Naoki drift builds |
| Swarm | 22 | Largest pack, diverse selection |
| WDTS | 11 | Wide Drift Tire Series |

## Local Development

```bash
# Clone repo
git clone https://github.com/realisimhq/ac-physics-tool.git
cd ac-physics-tool

# Serve locally
python3 -m http.server 8000 --directory docs

# Visit http://localhost:8000
```

## License

Physics data belongs to original carpack creators. Web application code is open source.

## Credits

**RealiSimHQ** - AC drift community and server hosting

**Carpack Creators:**
- BDC StreetSpec series
- DWG team
- Gravy Garage contributors  
- NNTS (Naoki)
- Swarm physics team
- WDTS creators

---

*For AC drift servers and community, visit RealiSimHQ*
