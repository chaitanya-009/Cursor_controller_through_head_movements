# config/settings.py
import json
import sys
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    "system": {
        "enable_analytics": False,
        "log_level": "info"
    },
    "head_tracking": {
        "enabled": True,
        "sensitivity_x": 0.1,
        "sensitivity_y": 0.05,
        "speed_gain_x": 120.0,
        "speed_gain_y": 150.0,
        "neutral_threshold_x": 0.08,
        "neutral_threshold_y": 0.05,
        "smoothness_factor": 0.3,
        "cursor_acceleration": 1.5,
        "deadzone_size": 0.08
    },
    "blink_detection": {
        "enabled": True,
        "ear_threshold": 0.16,
        "min_blink_frames": 3,
        "max_blink_frames": 8,
        "double_blink_timeout": 0.4,
        "cooldown": 0.2,
        "enable_sanity_check": True
    },
    "actions": {
        "single_blink_action": "left_click",
        "double_blink_action": "double_click",
        "long_blink_duration": 1.5,
        "click_hold_duration": 0.5
    },
    "ui": {
        "show_camera_preview": True,
        "cursor_visualization": True,
        "visual_feedback_color": "#ff0000",
        "mirror_camera": True,
        "show_fps": False
    }
}

CONFIG_FILE = os.path.join(
    sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__),
    'config.json'
)
VALIDATION_RANGES = {
    "head_tracking": {
        "sensitivity_x": (0.05, 0.3),
        "speed_gain_x": (50, 200),
        "smoothness_factor": (0.1, 0.9),
        "cursor_acceleration": (1.0, 3.0)
    },
    "blink_detection": {
        "ear_threshold": (0.1, 0.3),
        "double_blink_timeout": (0.2, 1.0)
    }
}

def load_config() -> Dict[str, Any]:
    """Load configuration with migration from old format"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            # Migrate old config format
            if "features" in config:
                config.setdefault("head_tracking", {})
                config["head_tracking"]["enabled"] = config["features"].get("head_tracking", True)
                config.setdefault("blink_detection", {})
                config["blink_detection"]["enabled"] = config["features"].get("blink_click", True)
                del config["features"]
            
            # Merge with default configuration
            merged_config = _deep_merge(DEFAULT_CONFIG, config)
            
            # Validate values
            merged_config = validate_config(merged_config)
            
            save_config(merged_config)  # Save migrated config
            return merged_config
            
    except (FileNotFoundError, json.JSONDecodeError):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration with validation"""
    validated_config = validate_config(config)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(validated_config, f, indent=4)

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure config values stay within safe ranges"""
    validated = config.copy()
    for section, keys in VALIDATION_RANGES.items():
        for key, (min_val, max_val) in keys.items():
            if section in validated and key in validated[section]:
                validated[section][key] = max(min_val, min(validated[section][key], max_val))
    return validated

def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries"""
    merged = base.copy()
    for key, value in update.items():
        if isinstance(value, dict) and key in merged:
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged