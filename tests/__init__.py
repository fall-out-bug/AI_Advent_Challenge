"""Local test package shim to override third-party `tests` namespace packages.

Ensures that `import tests` resolves to the repository test suite even when
dependencies expose their own `tests` namespace packages in site-packages.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Guarantee the repository test root is the first entry for the `tests` package.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
