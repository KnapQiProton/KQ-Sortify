import os
import sys
import shutil
import json
import uuid
import datetime
from pathlib import Path

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_bundle_dir():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG_PATH = os.path.join(get_app_dir(), "rules_config.json")
BUNDLE_CONFIG_PATH = os.path.join(get_bundle_dir(), "rules_config.json")
HISTORY_FILE_PATH = os.path.join(get_app_dir(), "history.json")

IGNORED_EXTENSIONS = {
    ".crdownload", ".tmp", ".part", ".opdownload", ".download", ".partial"
}

IGNORED_NAMES = {
    "desktop.ini", "thumbs.db", ".ds_store", "history.json",
    "rules_config.json", "sorter_engine.py", "app.py", "gui.py",
    "sortsensei.exe", "jalankan_sortsensei.bat", "run.bat", "dist", "build", "web",
    "sortsensei", "kq_sortify.exe", "kq sortify.exe", "kq_sortify", "kq sortify",
    "jalankan_kq_sortify.bat", "logo.png", "logo.ico",
    ".git", ".vscode", "node_modules", "__pycache__"
}

def load_rules(config_path=DEFAULT_CONFIG_PATH):
    # Try user-saved config next to executable first
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user rules config: {e}")
    
    # Fallback to bundled default config
    if os.path.exists(BUNDLE_CONFIG_PATH):
        try:
            with open(BUNDLE_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading bundled rules config: {e}")

    return {"categories": {}, "custom_rules": []}

def save_rules(rules_data, config_path=DEFAULT_CONFIG_PATH):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(rules_data, f, indent=2, ensure_ascii=False)

def format_size(bytes_size):
    if bytes_size is None or bytes_size < 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{bytes_size} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def get_folder_size(folder_path, max_items=250):
    total = 0
    count = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                try:
                    p = os.path.join(root, f)
                    total += os.path.getsize(p)
                    count += 1
                    if count >= max_items:
                        return total
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    return total

def classify_item(name, is_dir, rules):
    name_lower = name.lower()
    ext = os.path.splitext(name)[1].lower() if not is_dir else ""
    
    # 1. Custom rules matching
    for rule in rules.get("custom_rules", []):
        match_type = rule.get("match_type", "keyword")
        pattern = rule.get("pattern", "").lower()
        target_cat = rule.get("category")
        if not pattern or not target_cat:
            continue
        if match_type == "keyword" and pattern in name_lower:
            return target_cat, rule.get("folder_name", target_cat)
        elif match_type == "extension" and ext == pattern:
            return target_cat, rule.get("folder_name", target_cat)

    categories = rules.get("categories", {})

    # 2. Priority check: Kuliah (Keywords check first)
    if "Kuliah" in categories:
        kuliah_info = categories["Kuliah"]
        for kw in kuliah_info.get("keywords", []):
            if kw.lower() in name_lower:
                return "Kuliah", kuliah_info.get("folder_name", "Kuliah")

    # 3. Games (Keywords check)
    if "Games" in categories:
        games_info = categories["Games"]
        for kw in games_info.get("keywords", []):
            if kw.lower() in name_lower:
                return "Games", games_info.get("folder_name", "Games")

    # 4. Coding check (Keywords and Folders)
    if "Coding" in categories:
        coding_info = categories["Coding"]
        if is_dir:
            for kw in coding_info.get("keywords", []):
                if kw.lower() in name_lower:
                    return "Coding", coding_info.get("folder_name", "Coding")
        else:
            if ext in [e.lower() for e in coding_info.get("extensions", [])]:
                return "Coding", coding_info.get("folder_name", "Coding")

    # 5. Extension matching for other categories
    if not is_dir and ext:
        for cat_name, cat_info in categories.items():
            if cat_name in ["Kuliah", "Coding"]:
                continue
            ext_list = [e.lower() for e in cat_info.get("extensions", [])]
            if ext in ext_list:
                return cat_name, cat_info.get("folder_name", cat_name)

    # 6. Fallback checks for directories
    if is_dir:
        # Check if dir contains college keywords
        for cat_name in ["Kuliah", "Games", "Coding"]:
            if cat_name in categories:
                for kw in categories[cat_name].get("keywords", []):
                    if kw.lower() in name_lower:
                        return cat_name, categories[cat_name].get("folder_name", cat_name)
        return "Folders", "Folders"

    # 7. Fallback for Kuliah documents if not matched by keyword
    if ext in [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls"] and "Documents" in categories:
        return "Documents", categories["Documents"].get("folder_name", "Documents")

    return "Others", "Others"

def get_destination_folder(source_folder, target_mode, custom_target, subfolder_name):
    if target_mode == "custom" and custom_target:
        return os.path.join(custom_target, subfolder_name)
    elif target_mode == "subfolder":
        return os.path.join(source_folder, "Organized", subfolder_name)
    else:  # in_place
        return os.path.join(source_folder, subfolder_name)

def get_safe_destination_path(target_dir, file_name):
    base, ext = os.path.splitext(file_name)
    candidate = os.path.join(target_dir, file_name)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(target_dir, f"{base} ({counter}){ext}")
        counter += 1
    return candidate

def scan_directory(source_folder, target_mode="in_place", custom_target="", rules=None):
    if rules is None:
        rules = load_rules()
    
    source_path = Path(source_folder).resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise ValueError(f"Directory does not exist: {source_folder}")

    # Gather category folder names to avoid moving already organized category folders
    category_folder_names = set()
    for cat_name, info in rules.get("categories", {}).items():
        category_folder_names.add(info.get("folder_name", cat_name).lower())
    category_folder_names.add("organized")
    category_folder_names.add("others")
    category_folder_names.add("folders")

    items = []
    category_counts = {}
    total_size = 0

    try:
        with os.scandir(str(source_path)) as entries:
            for entry in entries:
                name = entry.name
                name_lower = name.lower()
                
                # Filter ignored system / temp / app files
                if name_lower in IGNORED_NAMES or name.startswith("~$") or name.startswith("."):
                    continue
                
                is_dir = entry.is_dir(follow_symlinks=False)
                ext = os.path.splitext(name)[1].lower() if not is_dir else ""

                if ext in IGNORED_EXTENSIONS:
                    continue

                # If it's an existing category folder in place, skip it
                if is_dir and name_lower in category_folder_names:
                    continue

                try:
                    stat = entry.stat(follow_symlinks=False)
                    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    if is_dir:
                        size = get_folder_size(entry.path)
                    else:
                        size = stat.st_size
                except Exception:
                    size = 0
                    mod_time = "-"

                category, subfolder_name = classify_item(name, is_dir, rules)
                dest_dir = get_destination_folder(str(source_path), target_mode, custom_target, subfolder_name)
                dest_path = os.path.join(dest_dir, name)

                # Skip if already in dest_dir
                if os.path.dirname(entry.path).lower() == dest_dir.lower():
                    continue

                cat_info = rules.get("categories", {}).get(category, {})
                color = cat_info.get("color", "#94a3b8")
                icon = cat_info.get("icon", "folder" if is_dir else "file")

                item = {
                    "id": str(uuid.uuid4())[:8],
                    "name": name,
                    "original_path": entry.path,
                    "target_dir": dest_dir,
                    "target_path": dest_path,
                    "is_dir": is_dir,
                    "extension": ext or ("DIR" if is_dir else ""),
                    "size_bytes": size,
                    "size_formatted": format_size(size),
                    "modified_time": mod_time,
                    "category": category,
                    "color": color,
                    "icon": icon,
                    "selected": True
                }

                items.append(item)
                total_size += size
                category_counts[category] = category_counts.get(category, 0) + 1
    except Exception as e:
        raise RuntimeError(f"Error scanning directory: {e}")

    # Sort items: Kuliah, Coding, Games, Archives, Documents, then others
    priority_order = {"Kuliah": 0, "Coding": 1, "Games": 2, "Archives": 3, "Documents": 4, "Images": 5}
    items.sort(key=lambda x: (priority_order.get(x["category"], 99), x["name"].lower()))

    return {
        "source_folder": str(source_path),
        "target_mode": target_mode,
        "custom_target": custom_target,
        "total_files": len(items),
        "total_size_bytes": total_size,
        "total_size_formatted": format_size(total_size),
        "category_counts": category_counts,
        "items": items
    }

def execute_organize(items_to_move, batch_id=None):
    if not batch_id:
        batch_id = str(uuid.uuid4())

    history = load_history()
    moved_records = []
    errors = []

    for item in items_to_move:
        src = item["original_path"]
        target_dir = item["target_dir"]

        if not os.path.exists(src):
            errors.append(f"File not found: {src}")
            continue

        try:
            os.makedirs(target_dir, exist_ok=True)
            safe_dest = get_safe_destination_path(target_dir, item["name"])
            shutil.move(src, safe_dest)
            
            moved_records.append({
                "original_path": src,
                "current_path": safe_dest,
                "name": item["name"],
                "is_dir": item.get("is_dir", False),
                "size_bytes": item.get("size_bytes", 0)
            })
        except Exception as e:
            errors.append(f"Failed to move {item['name']}: {str(e)}")

    if moved_records:
        batch_entry = {
            "batch_id": batch_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "moved_count": len(moved_records),
            "records": moved_records,
            "status": "active"
        }
        history.append(batch_entry)
        save_history(history)

    return {
        "batch_id": batch_id,
        "moved_count": len(moved_records),
        "errors": errors,
        "success": len(errors) == 0
    }

def move_to_custom_folder(items_to_move, folder_name, base_dir):
    """Move selected files into a user-named custom folder inside base_dir."""
    batch_id = str(uuid.uuid4())
    target_dir = os.path.join(base_dir, folder_name)

    history = load_history()
    moved_records = []
    errors = []

    for item in items_to_move:
        src = item["original_path"]

        if not os.path.exists(src):
            errors.append(f"File not found: {src}")
            continue

        try:
            os.makedirs(target_dir, exist_ok=True)
            safe_dest = get_safe_destination_path(target_dir, item["name"])
            shutil.move(src, safe_dest)

            moved_records.append({
                "original_path": src,
                "current_path": safe_dest,
                "name": item["name"],
                "is_dir": item.get("is_dir", False),
                "size_bytes": item.get("size_bytes", 0)
            })
        except Exception as e:
            errors.append(f"Failed to move {item['name']}: {str(e)}")

    if moved_records:
        batch_entry = {
            "batch_id": batch_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "moved_count": len(moved_records),
            "records": moved_records,
            "status": "active",
            "custom_folder": folder_name
        }
        history.append(batch_entry)
        save_history(history)

    return {
        "batch_id": batch_id,
        "moved_count": len(moved_records),
        "folder_name": folder_name,
        "target_dir": target_dir,
        "errors": errors,
        "success": len(errors) == 0
    }

def undo_last_batch(batch_id=None):
    history = load_history()
    if not history:
        return {"success": False, "message": "No history available to undo."}

    target_batch = None
    if batch_id:
        for b in reversed(history):
            if b.get("batch_id") == batch_id and b.get("status") == "active":
                target_batch = b
                break
    else:
        for b in reversed(history):
            if b.get("status") == "active":
                target_batch = b
                break

    if not target_batch:
        return {"success": False, "message": "No active batch found to undo."}

    reverted_records = []
    errors = []
    created_dirs = set()

    for rec in reversed(target_batch["records"]):
        curr = rec["current_path"]
        orig = rec["original_path"]
        
        if not os.path.exists(curr):
            errors.append(f"Cannot revert, file missing: {curr}")
            continue

        try:
            orig_parent = os.path.dirname(orig)
            os.makedirs(orig_parent, exist_ok=True)
            safe_orig = get_safe_destination_path(orig_parent, os.path.basename(orig))
            shutil.move(curr, safe_orig)
            reverted_records.append(rec)
            created_dirs.add(os.path.dirname(curr))
        except Exception as e:
            errors.append(f"Error reverting {rec['name']}: {str(e)}")

    # Clean up empty created directories
    for d in created_dirs:
        try:
            if os.path.exists(d) and not os.listdir(d):
                os.rmdir(d)
        except Exception:
            pass

    target_batch["status"] = "reverted"
    save_history(history)

    return {
        "success": True,
        "batch_id": target_batch["batch_id"],
        "reverted_count": len(reverted_records),
        "errors": errors
    }

def load_history():
    if os.path.exists(HISTORY_FILE_PATH):
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_last_undoable_batch():
    history = load_history()
    for b in reversed(history):
        if b.get("status") == "active":
            return {
                "batch_id": b["batch_id"],
                "timestamp": b["timestamp"],
                "moved_count": b["moved_count"]
            }
    return None
