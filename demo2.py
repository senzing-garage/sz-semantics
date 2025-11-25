#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` for gRPC client/server access to the Senzing SDK.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json
import logging
import pathlib

from sz_semantics import SzClient


if __name__ == "__main__":
    logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING)  # DEBUG

    # configure the Senzing SDK
    config: dict[str, dict] = {"sz": {"grpc_server": "localhost:8261"}}

    data_sources: dict[str, str] = {
        "CUSTOMERS": "data/truth/customers.json",
        "WATCHLIST": "data/truth/watchlist.json",
        "REFERENCE": "data/truth/reference.json",
    }

    sz: SzClient = SzClient(
        config,
        data_sources,
        debug=False,
    )

    # run entity resolution on the collection of datasets
    ents_batch: dict[str, str] = sz.entity_resolution(
        data_sources,
        debug=False,
    )

    print(json.dumps(ents_batch, indent=2))

    # serialize "GET_ENTITY" results on all entities as a JSONL file
    export_path: pathlib.Path = pathlib.Path("export.json")

    with open(export_path, mode="w", encoding="utf-8") as fp:
        for ent_json in sz.sz_engine.export_json_entity_report_iterator():
            fp.write(ent_json)
