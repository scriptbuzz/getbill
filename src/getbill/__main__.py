"""Allow running the tool with `python -m getbill`."""

import sys

from .cli import main

sys.exit(main())
