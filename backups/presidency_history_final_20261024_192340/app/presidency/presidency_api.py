from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import tempfile
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request

from app.auth.session import get_current_member_id


presidency_bp = Blueprint("presidency", __name__)

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR / "data" / "presidency" / "officials.json"
)

BACKUP_DIR = (
    BASE_DIR / "backups" / "presidency"
)

HISTORY_FILE = BASE_DIR / "data" / "presidency" / "official_history.json"
HISTORY_BACKUP_DIR = BASE_DIR / "backups" / "presidency" / "history"


# Matches the TLC account used by the existing privileged system routes.
AUTHORIZED_EDITOR_MEMBER_ID = "TLC/001/2026"

POSITION_SLOTS = [
    {
        "key": "CHAIRPERSON",
        "position_id": "TLC-POS-001",
        "position": "Chairperson",
        "order": 1,
    },
    {
        "key": "VICE_CHAIRPERSON",
        "position_id": "TLC-POS-002",
        "position": "Vice Chairperson",
        "order": 2,
    },
    {
        "key": "SECRETARY",
        "position_id": "TLC-POS-003",
        "position": "Secretary",
        "order": 3,
    },
    {
        "key": "TREASURER",
        "position_id": "TLC-POS-004",
        "position": "Treasurer",
        "order": 4,
    },
]

EDITABLE_FIELDS = (
    "name",
    "member_id",
    "email",
    "contact",
    "photo_url",
    "term_start",
    "term_end",
    "status",
    "biography",
)


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _current_member_id():
    return str(get_current_member_id() or "").strip().upper()


def _is_authorized_editor():
    return _current_member_id() == AUTHORIZED_EDITOR_MEMBER_ID


def _default_state():
    return {
        "schema_version": 1,
        "updated_at": None,
        "updated_by": None,
        "officials": [
            {
                **position,
                "name": "",
                "member_id": "",
                "email": "",
                "contact": "",
                "photo_url": "",
                "term_start": "",
                "term_end": "",
                "status": "VACANT",
                "biography": "",
            }
            for position in POSITION_SLOTS
        ],
    }


def _read_state():
    if not DATA_FILE.exists():
        return _default_state()

    with DATA_FILE.open("r", encoding="utf-8-sig") as handle:
        saved = json.load(handle)

    if not isinstance(saved, dict):
        raise ValueError("Presidency data must be a JSON object.")

    saved_officials = saved.get("officials", [])

    if not isinstance(saved_officials, list):
        raise ValueError("Presidency officials must be a JSON list.")

    by_key = {
        str(item.get("key", "")).strip().upper(): item
        for item in saved_officials
        if isinstance(item, dict)
    }

    state = _default_state()

    for official in state["officials"]:
        saved_official = by_key.get(official["key"], {})

        for field in EDITABLE_FIELDS:
            value = saved_official.get(field)

            if isinstance(value, str):
                official[field] = value

    state["updated_at"] = saved.get("updated_at")
    state["updated_by"] = saved.get("updated_by")

    return state


def _save_state(state):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_file = BACKUP_DIR / f"officials_before_{stamp}.json"
        shutil.copy2(DATA_FILE, backup_file)

    temporary_path = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix="officials_",
            suffix=".tmp",
            dir=str(DATA_FILE.parent),
        )

        temporary_path = Path(temporary_name)

        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                state,
                handle,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, DATA_FILE)

    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
        raise


def _text_field(value, maximum_length):
    if value is None:
        return ""

    if not isinstance(value, str):
        return None

    value = value.strip()

    if len(value) > maximum_length:
        return None

    if any(ord(char) < 32 and char not in "\r\n\t" for char in value):
        return None

    return value


def _valid_photo_url(value):
    if not value:
        return True

    if value.startswith("/assets/") or value.startswith("/uploads/"):
        parts = value.split("/")
        return (
            "\\" not in value
            and ".." not in parts
            and not any(ord(char) < 32 for char in value)
        )

    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.netloc)
            and parsed.username is None
            and parsed.password is None
            and not any(ord(char) < 32 for char in value)
        )
    except ValueError:
        return False


def _validated_date(value):
    if value == "":
        return ""

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None



# TLC-PRESIDENCY-HISTORY-ARCHIVE-V1

def _history_default():
    return {
        "schema_version": 1,
        "updated_at": None,
        "updated_by": None,
        "records": [],
    }


def _read_history():
    if not HISTORY_FILE.exists():
        return _history_default()

    with HISTORY_FILE.open("r", encoding="utf-8-sig") as handle:
        saved = json.load(handle)

    if not isinstance(saved, dict):
        raise ValueError("Presidency history must be a JSON object.")

    records = saved.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Presidency history records must be a list.")

    saved["schema_version"] = 1
    saved["records"] = records
    return saved


def _history_id(official):
    position_key = str(official.get("key", "")).strip().upper()
    member_id = str(official.get("member_id", "")).strip().casefold()
    name = str(official.get("name", "")).strip().casefold()
    identity = member_id or name
    term_start = str(official.get("term_start", "")).strip() or "UNDATED"

    return "|".join((position_key, identity, term_start))


def _save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if HISTORY_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        shutil.copy2(
            HISTORY_FILE,
            HISTORY_BACKUP_DIR / f"official_history_before_{stamp}.json",
        )

    history["updated_at"] = _now()
    history["updated_by"] = _current_member_id()

    temp_path = HISTORY_FILE.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(history, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        os.replace(temp_path, HISTORY_FILE)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _archive_official_record(official, reason):
    if not isinstance(official, dict):
        return False

    name = str(official.get("name", "")).strip()
    status = str(official.get("status", "")).strip().upper()

    if not name or status == "VACANT":
        return False

    history = _read_history()
    identifier = _history_id(official)

    # Prevent repeated edits from producing duplicate service records.
    if any(
        str(record.get("history_id", "")) == identifier
        for record in history["records"]
        if isinstance(record, dict)
    ):
        return False

    archived = dict(official)
    archived["history_id"] = identifier
    archived["status"] = "FORMER"
    archived["archive_reason"] = str(reason)
    archived["archived_at"] = _now()
    archived["archived_by"] = _current_member_id()

    history["records"].append(archived)
    _save_history(history)
    return True


@presidency_bp.route(
    "/api/member/presidency",
    methods=["GET"],
)
def get_presidency_directory():
    if not _current_member_id():
        return jsonify({
            "success": False,
            "message": "Please sign in to view the TLC officials directory.",
        }), 401

    try:
        state = _read_state()
        # TLC_CONTACT_FIELDS_READ_V2
        if DATA_FILE.exists():
            with DATA_FILE.open('r', encoding='utf-8-sig') as _contact_handle:
                _contact_saved = json.load(_contact_handle)
            _contact_records = _contact_saved.get('officials', [])
            _contact_by_key = {
                str(item.get('key', '')).upper(): item
                for item in _contact_records
                if isinstance(item, dict)
            }
            for _contact_official in state.get('officials', []):
                _contact_key = str(_contact_official.get('key', '')).upper()
                _contact_record = _contact_by_key.get(_contact_key, {})
                _contact_official['email'] = _contact_record.get(
                    'email', _contact_official.get('email', '')
                ) or ''
                _contact_official['contact'] = _contact_record.get(
                    'contact', _contact_official.get('contact', '')
                ) or ''

        for _presidency_official in state.get("officials", []):
            if isinstance(_presidency_official, dict):
                _presidency_official.setdefault("email", "")
                _presidency_official.setdefault("contact", "")

        return jsonify({
            "success": True,
            "officials": state["officials"],
            "updated_at": state["updated_at"],
            "can_manage": _is_authorized_editor(),
        })

    except Exception as error:
        print(
            "[TLC PRESIDENCY] Read error:",
            repr(error),
            flush=True,
        )

        return jsonify({
            "success": False,
            "message": "The officials directory could not be loaded.",
        }), 500



@presidency_bp.route("/api/member/presidency/history", methods=["GET"])
def get_presidency_history():
    if not _current_member_id():
        return jsonify({
            "success": False,
            "message": "Please sign in to view the leadership archive.",
        }), 401

    try:
        history = _read_history()
        records = [
            item for item in history["records"]
            if isinstance(item, dict)
        ]

        records.sort(
            key=lambda item: (
                str(item.get("term_end", "")),
                str(item.get("term_start", "")),
                str(item.get("archived_at", "")),
            ),
            reverse=True,
        )

        return jsonify({
            "success": True,
            "records": records,
            "updated_at": history.get("updated_at"),
        })
    except Exception:
        return jsonify({
            "success": False,
            "message": "The leadership archive could not be loaded.",
        }), 500


@presidency_bp.route(
    "/api/presidency/officials/<position_key>",
    methods=["PUT"],
)
def update_presidency_official(position_key):
    if not _current_member_id():
        return jsonify({
            "success": False,
            "message": "Authentication required.",
        }), 401

    if not _is_authorized_editor():
        return jsonify({
            "success": False,
            "message": "You are not authorized to manage TLC officials.",
        }), 403

    position_key = str(position_key or "").strip().upper()

    position = next(
        (
            item for item in POSITION_SLOTS
            if item["key"] == position_key
        ),
        None,
    )

    if position is None:
        return jsonify({
            "success": False,
            "message": "Unknown official position.",
        }), 404

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request is required.",
        }), 400

    values = {}

    limits = {
        "name": 120,
        "member_id": 40,
        "email": 254,
        "contact": 40,
        "photo_url": 500,
        "term_start": 10,
        "term_end": 10,
        "status": 20,
        "biography": 1200,
    }

    for field in EDITABLE_FIELDS:
        value = _text_field(payload.get(field, ""), limits[field])

        if value is None:
            return jsonify({
                "success": False,
                "message": f"The {field.replace('_', ' ')} field is invalid or too long.",
            }), 400

        values[field] = value

    email_value = values.get("email", "").strip()
    if email_value and (
        email_value.count("@") != 1
        or any(character.isspace() for character in email_value)
        or "." not in email_value.rsplit("@", 1)[1]
    ):
        return jsonify({
            "success": False,
            "message": "Enter a valid official email address.",
        }), 400

    status = values["status"].upper()

    if status not in ("ACTIVE", "FORMER", "VACANT"):
        return jsonify({
            "success": False,
            "message": "Status must be Active, Former, or Vacant.",
        }), 400

    if not _valid_photo_url(values["photo_url"]):
        return jsonify({
            "success": False,
            "message": (
                "Use an HTTPS photo URL or a portal asset path "
                "such as /assets/profile_pictures/photo.jpg."
            ),
        }), 400

    start_date = _validated_date(values["term_start"])
    end_date = _validated_date(values["term_end"])

    if start_date is None or end_date is None:
        return jsonify({
            "success": False,
            "message": "Term dates must use the YYYY-MM-DD format.",
        }), 400

    if start_date and end_date and end_date < start_date:
        return jsonify({
            "success": False,
            "message": "The term end date cannot be earlier than its start date.",
        }), 400

    values["term_start"] = start_date
    values["term_end"] = end_date
    values["status"] = status

    if status == "VACANT":
        values.update({
            "name": "",
            "member_id": "",
            "email": "",
            "contact": "",
            "photo_url": "",
            "term_start": "",
            "term_end": "",
            "biography": "",
        })
    elif not values["name"]:
        return jsonify({
            "success": False,
            "message": "Enter the official's name or select Vacant.",
        }), 400

    try:
        state = _read_state()
        for _presidency_official in state.get("officials", []):
            if isinstance(_presidency_official, dict):
                _presidency_official.setdefault("email", "")
                _presidency_official.setdefault("contact", "")

        official = next(
            (
                item for item in state["officials"]
                if item["key"] == position_key
            ),
            None,
        )

        if official is None:
            raise ValueError("The requested official position is unavailable.")

        # TLC-ARCHIVE-OUTGOING-OFFICIAL-V1
        old_official = dict(official)
        old_name = str(old_official.get("name", "")).strip()
        new_name = str(values.get("name", "")).strip()
        old_member_id = str(old_official.get("member_id", "")).strip()
        new_member_id = str(values.get("member_id", "")).strip()
        
        name_changed = bool(
            old_name and new_name
            and old_name.casefold() != new_name.casefold()
        )
        member_changed = bool(
            old_member_id and new_member_id
            and old_member_id.casefold() != new_member_id.casefold()
        )
        new_status = str(values.get("status", "")).strip().upper()
        
        outgoing_official = bool(old_name) and (
            new_status in ("FORMER", "VACANT")
            or name_changed
            or member_changed
        )
        
        if outgoing_official:
            if new_status == "VACANT":
                archive_reason = "Office made vacant by authorized administration"
            elif new_status == "FORMER":
                archive_reason = "Official marked former by authorized administration"
            else:
                archive_reason = "Outgoing office holder replaced"
        
            _archive_official_record(old_official, archive_reason)
        
        official.update(values)

        state["updated_at"] = _now()
        state["updated_by"] = _current_member_id()

        _save_state(state)

        print(
            "[TLC PRESIDENCY] Official updated:",
            position_key,
            "by",
            _current_member_id(),
            flush=True,
        )

        return jsonify({
            "success": True,
            "message": f"{position['position']} record updated successfully.",
            "official": official,
            "updated_at": state["updated_at"],
        })

    except Exception as error:
        print(
            "[TLC PRESIDENCY] Update error:",
            repr(error),
            flush=True,
        )

        return jsonify({
            "success": False,
            "message": "The official record could not be saved.",
        }), 500
