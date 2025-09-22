#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate a key/value store.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

class KeyValueStore:  # pylint: disable=R0903
    """
Generate a key/value store, aka a Python `dict` -- which a given use
case can override to use a scalable alternative if needed.
    """

    def allocate (
        self,
        ) -> dict:
        """
Override if you want to use an alternative to the Python built-in
`dict` data structure.
        """
        return {}
