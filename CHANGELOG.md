# Changelog

All notable changes to ScreenSeek are documented here.

---

## [1.0.0] — 2026-06-13

### Added

**Core**
- OCR engine with EasyOCR (primary) and Tesseract (fallback)
- Automatic fallback between OCR engines
- Confidence score and language detection per image
- Image pre-processing (contrast boost, sharpening, upscaling)

**Database**
- SQLite database with WAL journal mode
- Full-text search index via SQLite FTS5
- Auto-sync triggers keeping FTS index consistent
- `screenshots`, `folders`, `settings` tables
- File-hash based change detection (skip unchanged images)

**Search**
- Phrase matching (`"exact phrase"`)
- Partial/prefix matching (`conf` matches `confirmation`)
- Multi-word AND search
- Case-insensitive matching
- Results ranked by BM25 relevance
- Filter by folder, date range, file type
- LIKE fallback for malformed FTS queries

**Indexing**
- Multi-threaded indexing pipeline (ThreadPoolExecutor)
- Cancellable indexing
- Auto-purge of deleted files
- Force reindex option
- Per-folder indexing support

**Thumbnail Generation**
- WEBP thumbnail cache (configurable size: 64–512 px)
- Deterministic cache path (hash-based)
- Lazy generation

**Folder Monitoring**
- Real-time folder watching via Watchdog
- Automatic OCR + index of new screenshots
- Auto-removal of deleted screenshots from index
- File move detection

**User Interface**
- PySide6 dark/light theme with full stylesheet
- Search bar with 300 ms debounce
- Scrollable grid results panel with thumbnail cards
- Right-side preview panel with full image, metadata, OCR text
- Left sidebar with folder list, quick filters, statistics
- Settings dialog (theme, OCR languages, thumbnail size, monitoring)
- Progress bar during indexing
- Status bar with live screenshot count
- Open image / Show in Explorer actions
- Copy extracted text to clipboard
- Keyboard shortcuts (Ctrl+O, Ctrl+Q, Ctrl+,)

**Packaging & Release**
- PyInstaller spec for Windows `.exe`
- BuildBox-compatible `buildbox.json` manifest
- Application icon (`.ico`) in multiple sizes
- Logo variants (512 / 256 / 128 / 64 / 32 px)
- Placeholder screenshots for store listing

**Testing**
- pytest suite: OCR, database, search, thumbnails, indexer
- Mocked OCR in integration-style tests

---

## [Unreleased]

### Planned
- Semantic vector search (v2.0)
- Natural language queries (v3.0)
- Screenshot auto-categorisation (v4.0)
- Cross-device sync (v5.0, opt-in, encrypted)
