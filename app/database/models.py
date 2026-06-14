"""
SQLite schema definition — each entry in ALL_STATEMENTS is a single executable SQL statement.
"""

SCHEMA_VERSION = 1

CREATE_SCREENSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS screenshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT    NOT NULL UNIQUE,
    file_name       TEXT    NOT NULL,
    folder          TEXT    NOT NULL,
    file_hash       TEXT    NOT NULL,
    file_size       INTEGER NOT NULL DEFAULT 0,
    created_at      REAL    NOT NULL,
    modified_at     REAL    NOT NULL,
    indexed_at      REAL    NOT NULL,
    ocr_text        TEXT    DEFAULT '',
    ocr_confidence  REAL    DEFAULT 0.0,
    language        TEXT    DEFAULT 'unknown',
    thumbnail_path  TEXT    DEFAULT '',
    engine_used     TEXT    DEFAULT 'none'
)
"""

CREATE_FOLDERS_TABLE = """
CREATE TABLE IF NOT EXISTS folders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    NOT NULL UNIQUE,
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  REAL    NOT NULL
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
)
"""

CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS screenshots_fts
USING fts5(
    file_name,
    ocr_text,
    content='screenshots',
    content_rowid='id',
    tokenize='unicode61'
)
"""

CREATE_TRIGGER_AI = """
CREATE TRIGGER IF NOT EXISTS screenshots_ai AFTER INSERT ON screenshots BEGIN
    INSERT INTO screenshots_fts(rowid, file_name, ocr_text)
    VALUES (new.id, new.file_name, new.ocr_text);
END
"""

CREATE_TRIGGER_AD = """
CREATE TRIGGER IF NOT EXISTS screenshots_ad AFTER DELETE ON screenshots BEGIN
    INSERT INTO screenshots_fts(screenshots_fts, rowid, file_name, ocr_text)
    VALUES ('delete', old.id, old.file_name, old.ocr_text);
END
"""

CREATE_TRIGGER_AU = """
CREATE TRIGGER IF NOT EXISTS screenshots_au AFTER UPDATE ON screenshots BEGIN
    INSERT INTO screenshots_fts(screenshots_fts, rowid, file_name, ocr_text)
    VALUES ('delete', old.id, old.file_name, old.ocr_text);
    INSERT INTO screenshots_fts(rowid, file_name, ocr_text)
    VALUES (new.id, new.file_name, new.ocr_text);
END
"""

INDEX_FOLDER     = "CREATE INDEX IF NOT EXISTS idx_screenshots_folder      ON screenshots(folder)"
INDEX_HASH       = "CREATE INDEX IF NOT EXISTS idx_screenshots_file_hash   ON screenshots(file_hash)"
INDEX_INDEXED_AT = "CREATE INDEX IF NOT EXISTS idx_screenshots_indexed_at  ON screenshots(indexed_at)"
INDEX_MODIFIED   = "CREATE INDEX IF NOT EXISTS idx_screenshots_modified_at ON screenshots(modified_at)"

DEFAULT_SETTINGS = [
    ("theme", "dark"),
    ("ocr_languages", "en"),
    ("thumbnail_size", "256"),
    ("db_path", ""),
    ("start_on_boot", "false"),
    ("monitor_enabled", "true"),
    ("schema_version", str(SCHEMA_VERSION)),
]

# Each entry is a single, complete SQL statement — no semicolon splitting needed.
ALL_STATEMENTS = [
    CREATE_SCREENSHOTS_TABLE,
    CREATE_FOLDERS_TABLE,
    CREATE_SETTINGS_TABLE,
    CREATE_FTS_TABLE,
    CREATE_TRIGGER_AI,
    CREATE_TRIGGER_AD,
    CREATE_TRIGGER_AU,
    INDEX_FOLDER,
    INDEX_HASH,
    INDEX_INDEXED_AT,
    INDEX_MODIFIED,
]
