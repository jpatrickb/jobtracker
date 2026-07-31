"""Global config file: remembers a default data directory so `jobtracker` works from anywhere
without `cd`-ing into a specific data directory first (see store.data_root()'s third resolution
tier). Written by `jobtracker setup`; read by every other command as a fallback."""
import os
from pathlib import Path

CONFIG_DIRNAME = "jobtracker"
CONFIG_FILENAME = "config.toml"


def config_dir():
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).resolve() if xdg else Path.home() / ".config"
    return base / CONFIG_DIRNAME


def config_path():
    return config_dir() / CONFIG_FILENAME


def read_default_data_root():
    """The data_root recorded by a prior `jobtracker setup`, or None if none is set yet."""
    path = config_path()
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("data_root"):
            _, _, value = line.partition("=")
            return Path(value.strip().strip('"')).expanduser()
    return None


def write_default_data_root(data_root):
    """Record `data_root` as the default, creating the config directory if needed. Overwrites
    any prior value -- re-running `jobtracker setup` with a new location is meant to replace it,
    not merge with it."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'data_root = "{Path(data_root).resolve()}"\n')
