import os
import zipfile
import shutil
from pathlib import Path

repo_root = Path(r"d:\VIT")
backend_dir = repo_root / "member1-ml" / "backend"
frontend_dir = repo_root / "member2-gis" / "frontend"

out_backend_zip = repo_root / "backend.zip"
out_frontend_zip = repo_root / "frontend.zip"
out_combined_zip = repo_root / "vit_mapathon_frontend_and_backend.zip"

# Exclusions
EXCLUDE_DIRS = {"node_modules", ".git", "__pycache__", ".pytest_cache", ".venv", "env"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd"}

def should_include(file_path: Path) -> bool:
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False
    if file_path.suffix in EXCLUDE_EXTS:
        return False
    return True

print("Creating backend.zip...")
with zipfile.ZipFile(out_backend_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(backend_dir):
        # filter dirs in place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            fp = Path(root) / f
            if should_include(fp):
                arcname = fp.relative_to(backend_dir.parent)  # e.g. backend/...
                z.write(fp, arcname)

print("Creating frontend.zip...")
with zipfile.ZipFile(out_frontend_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(frontend_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            fp = Path(root) / f
            if should_include(fp):
                arcname = fp.relative_to(frontend_dir.parent)  # e.g. frontend/...
                z.write(fp, arcname)

print("Creating vit_mapathon_frontend_and_backend.zip...")
with zipfile.ZipFile(out_combined_zip, "w", zipfile.ZIP_DEFLATED) as z:
    # Add backend
    for root, dirs, files in os.walk(backend_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            fp = Path(root) / f
            if should_include(fp):
                arcname = Path("backend") / fp.relative_to(backend_dir)
                z.write(fp, arcname)

    # Add frontend
    for root, dirs, files in os.walk(frontend_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            fp = Path(root) / f
            if should_include(fp):
                arcname = Path("frontend") / fp.relative_to(frontend_dir)
                z.write(fp, arcname)

print(f"backend.zip: {out_backend_zip.stat().st_size:,} bytes")
print(f"frontend.zip: {out_frontend_zip.stat().st_size:,} bytes")
print(f"combined.zip: {out_combined_zip.stat().st_size:,} bytes")
print("Packaging complete!")
