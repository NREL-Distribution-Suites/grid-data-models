"""Snapshot serialization helpers for SQLite GDM persistence."""

from __future__ import annotations

import base64
import io
import json
import tempfile
import zipfile
from pathlib import Path


def _serialize_system_to_json_text(system) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_json = Path(tmp_dir) / "system.json"
        system.to_json(temp_json, overwrite=True)
        system_json = temp_json.read_text()
        parsed = json.loads(system_json)
        time_series_dir = parsed.get("time_series", {}).get("directory")
        time_series_zip_b64 = None
        if time_series_dir:
            sidecar_dir = Path(tmp_dir) / time_series_dir
            if sidecar_dir.exists():
                time_series_zip_b64 = _zip_directory_to_base64(sidecar_dir)

        snapshot = {
            "snapshot_format": "gdm-sqlite-v1",
            "system_json": system_json,
            "time_series_directory": time_series_dir,
            "time_series_zip_b64": time_series_zip_b64,
        }
        return json.dumps(snapshot)


def _decode_snapshot_payload(payload: str) -> dict[str, str | None]:
    parsed = json.loads(payload)
    if isinstance(parsed, dict) and parsed.get("snapshot_format") == "gdm-sqlite-v1":
        return {
            "system_json": parsed["system_json"],
            "time_series_directory": parsed.get("time_series_directory"),
            "time_series_zip_b64": parsed.get("time_series_zip_b64"),
        }

    return {
        "system_json": payload,
        "time_series_directory": None,
        "time_series_zip_b64": None,
    }


def _zip_directory_to_base64(directory: Path) -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, arcname=str(file_path.relative_to(directory)))
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _restore_time_series_sidecar(base_dir: Path, snapshot: dict[str, str | None]) -> None:
    ts_directory = snapshot.get("time_series_directory")
    ts_zip_b64 = snapshot.get("time_series_zip_b64")
    if not ts_directory or not ts_zip_b64:
        return

    destination = base_dir / ts_directory
    destination.mkdir(parents=True, exist_ok=True)
    content = base64.b64decode(ts_zip_b64.encode("utf-8"))
    with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
        archive.extractall(destination)
