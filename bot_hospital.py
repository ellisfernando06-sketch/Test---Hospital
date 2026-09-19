# -*- coding: utf-8 -*-
"""Auto-restore: en el primer arranque expande el bot completo y pide reinicio."""
import base64
import gzip
import pathlib
import sys

_B64 = (
    "H4sIAIYVrmoC/+19a28k13Xgd/6Km5IBdo2pntHDTkybjltkz4j2DHvU5GghMESr2F3k1Ki7q13VTWnM"
    "JSAHSRbYvJBIQbDKBlobSLDerIAFtAsE+rLA8p9of8DqJ+x53Ge9uvpBzsSWkHjYVbfu49zzvuee43ne"
    "xmk87T2N00k0DYbNyfONncx/G2/FUzEIxV6U9uNkICZBEojZWKRhchEN4gTfJfEwnAyD50J1FCRRvCX6"
    "8RhabqRROg1HATachMkoSuNUTOBD74PweeqJxnAYXISpDz2eX381FuFQ9IPkPMb2/WAQiJ/PonC8vbEh"
    "4L/Ovztod0Xlf6/+GAeewpzENIa50He7nR5/ele0D3Zb3QetvU5vb/9wd//xw/2DVua7YDCKxjDrJJhG"
    "FzF1sLffbe8edbq9O6JBsxpESdjvR9dfjn1n5FEwHsACYfLpzGpEnfy0fb/d22s/bnWPWo/aB0cdmM7h"
    "k8ft7rv7h51uSR/j6CLkRRwete7fr7F4+fnp9a/SqB+nGxtHMUx4GOD6zqLzWRLQlMQF9CzCsXwMmy++"
    "/vhTEaa4BdefHezvdkSQ9J8CCGAPwo1x2A9T2F14P4B/EkYFgMUEf8A3gEoiENOZxo3mxkY3hO2Dr+J0"
    "m9YwiSYiGqewL0PxaiISfJ2Eo3A8TZvTj6YbG63xNKSlh8/C/gx65u9ea4r2WHSDaPgh4FkjxmEA26bR"
    "+NzfFu8CwgWnQ/jw6z/7W3HU+Vn7QOyIH03jD2B5A57ajzckjBrTYHQaXf9mLIJ+CHMXiAed7l6Pv7sr"
    "3uoc8d9+Uxw8AXRBICFaXn85iM7jJnX0elO0ns1gIQZ822Icj04Tnj7SRAq4AjQQjuJnkb8FTwFiMDgs"
    "Nk631HT291JG9XEw5E+H8blII/gnFbM0SHm8N5piLwRMiIGGxOMY+hnSYh8n0UU0DM/DgXgQTEOEzj6A"
)