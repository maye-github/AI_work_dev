# -*- coding: utf-8 -*-
"""RAG knowledge-base tooling for the legacy R60 cards.

Design references:
  docs/95_legacy/r60/learning-plan-3modules.md §6

The corpus is split by ``corpus_scope`` into physically separate SQLite
databases so that a holdout exam (R60Login implementation) can never be
retrieved while teaching material is in use.
"""

__version__ = "0.1.0"
