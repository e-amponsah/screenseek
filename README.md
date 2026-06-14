# ScreenSeek

> **Search your screenshots like Google searches the web.**

ScreenSeek is a desktop productivity application that lets you instantly search through thousands of screenshots stored on your computer — by the text *inside* them.

---

## The Problem

You saved something important as a screenshot. Now you can't remember:

- the filename
- which folder it's in
- what date you took it

You scroll through hundreds of images. It takes minutes.

**ScreenSeek reduces that to seconds.**

---

## How It Works

1. **Add folders** containing your screenshots
2. ScreenSeek **OCR-indexes every image** in the background
3. You **search by text** — any phrase, word, or fragment you remember seeing
4. Results appear **instantly**, with thumbnails and extracted text

All processing is **100% local**. No screenshot data ever leaves your machine.

---

## Features

| Feature | Details |
|---|---|
| OCR Engine | EasyOCR (primary) + Tesseract (fallback) |
| Search | SQLite FTS5 — phrase, partial, multi-word |
| File Formats | PNG, JPG, JPEG, WEBP, BMP, TIFF, HEIC |
| Monitoring | Real-time folder watching via Watchdog |
| Thumbnails | Optimised WEBP cache |
| Theme | Dark / Light / System |
| Privacy | Zero telemetry, zero cloud, fully offline |

---

## Architecture

```
screenseek/
├── app/
│   ├── ocr/           # EasyOCR + Tesseract wrappers
│   ├── database/      # SQLite schema + DatabaseManager
│   ├── search/        # FTS5 search engine
│   ├── thumbnails/    # WEBP thumbnail cache
│   ├── watcher/       # Watchdog folder monitor
│   ├── settings/      # Typed settings manager
│   ├── indexer.py     # Orchestration pipeline
│   └── ui/            # PySide6 interface
├── tests/             # pytest test suite
├── assets/            # Logo, icons, screenshots
├── docs/              # Documentation
├── release/           # Build artefacts
├── main.py            # Entry point
├── requirements.txt
└── buildbox.json
```

---

## Installation

### Prerequisites

- Python 3.10+
- Tesseract OCR (optional fallback): [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

### Install

```bash
git clone https://github.com/screenseek/screenseek.git
cd screenseek
pip install -r requirements.txt
python main.py
```

---

## Usage

1. Launch ScreenSeek
2. Click **File > Add Folder** or **+ Add Folder** in the sidebar
3. Select your screenshots folder (e.g., `Pictures`, `Downloads`, `Desktop`)
4. ScreenSeek begins indexing automatically
5. Type any text you remember in the search bar
6. Click a result to preview it; use **Open Image** or **Show in Explorer**

### Search Tips

| Query | Matches |
|---|---|
| `AF1234` | Any screenshot containing "AF1234" |
| `flight paris` | Screenshots with both words |
| `"hotel confirmation"` | Exact phrase |
| `OTP` | Screenshots containing "OTP" |

---

## Building the Windows Executable

```bash
pip install pyinstaller
pyinstaller screenseek.spec
```

The output is `release/ScreenSeek.exe` — a self-contained Windows executable.

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Privacy Statement

ScreenSeek is designed with privacy as a core principle:

- **No internet connection required**
- **No telemetry or analytics**
- **No user tracking**
- **No screenshot uploads**
- All data stored in `~/.screenseek/` on your local machine

---

## Roadmap

| Version | Feature |
|---|---|
| v1.0 | Text-based OCR search (current) |
| v2.0 | Semantic AI search (search by meaning) |
| v3.0 | Natural language queries |
| v4.0 | Automatic screenshot categorisation |
| v5.0 | Cross-device synchronisation (opt-in, encrypted) |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for students, researchers, developers, and professionals who save their digital life as screenshots.*
