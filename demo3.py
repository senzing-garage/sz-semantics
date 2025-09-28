#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` for gRPC client/server access to the Senzing SDK.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json
import logging
import pathlib
import tomllib
import typing

from sz_semantics import Mask, SzClient


if __name__ == "__main__":
    config_path: pathlib.Path = pathlib.Path("config.toml")

    with open(config_path, mode = "rb") as fp:
        config: dict = tomllib.load(fp)

    logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(level = logging.WARNING) # DEBUG

    data_sources: typing.Dict[ str, str ] = {
        "CUSTOMERS": "data/truth/customers.json",
        "WATCHLIST": "data/truth/watchlist.json",
        "REFERENCE": "data/truth/reference.json",
    }

    # configure the Senzing SDK
    sz: SzClient = SzClient(
        config,
        data_sources,
        debug = False,
    )

    # run entity resolution on the collection of datasets
    ents: dict = sz.entity_resolution(
        data_sources,
        debug = False,
    )

    print(json.dumps(ents, indent = 2))
