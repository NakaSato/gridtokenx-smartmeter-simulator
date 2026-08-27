"""Shared pytest fixtures.

`get_config()` hands out a module-level singleton, and `engine.config` is that
same object -- so a test that flips a flag on it (`transformer_oltc_enabled`,
`freq_droop_enabled`, `pv_voltvar_enabled`, ...) leaves it flipped for every
test that runs afterwards. Several tests do exactly that. Restore the config
around every test so the order tests run in cannot change what they assert.
"""

import pytest

from smart_meter_simulator.config import settings
from smart_meter_simulator.config.settings import get_config


@pytest.fixture(autouse=True)
def restore_config():
    """Snapshot the config singleton's fields and put them back afterwards.

    Also restores the singleton *pointer*: tests that need a config built from
    patched env null `settings._config_instance` to force a rebuild, and would
    otherwise leave the replacement — built from env that monkeypatch has since
    reverted — in place for every test after them.
    """
    original_instance = settings._config_instance
    config = get_config()
    before = {name: getattr(config, name) for name in type(config).model_fields}
    try:
        yield config
    finally:
        settings._config_instance = original_instance
        for name, value in before.items():
            if getattr(config, name) != value:
                setattr(config, name, value)
