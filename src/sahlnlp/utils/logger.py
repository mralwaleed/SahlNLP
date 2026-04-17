"""
Centralized logging for SahlNLP.

Uses Python's standard logging library with a NullHandler by default.
Users opt in by configuring the 'sahlnlp' logger in their own code.
"""

import logging

# Package-level logger — silent by default (NullHandler).
# Users enable logging via: logging.getLogger('sahlnlp').setLevel(logging.DEBUG)
logger = logging.getLogger('sahlnlp')
logger.addHandler(logging.NullHandler())
