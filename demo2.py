#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` to mask PII values in Senzing JSON.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import logging
import pathlib

from sz_semantics import Thesaurus


if __name__ == "__main__":
    logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(level = logging.WARNING) # DEBUG

    ## choose your adventure: multiple datasets and their ER exports
    context: str = "truth" # "open" "strw"

    match context:
        case "truth":
            export_path: pathlib.Path = pathlib.Path("data/truth/export.json")

            datasets: list = [
                "data/truth/customers.json",
                "data/truth/reference.json",
                "data/truth/watchlist.json",
            ]
        case "open":
            export_path = pathlib.Path("data/open/export.json")

            datasets = [
                "data/open/open-ownership.json",
                "data/open/open-sanctions.json",
            ]
        case "strw":
            export_path = pathlib.Path("data/strw/export.json")

            datasets = [
                "data/strw/acme_biz.json",
                "data/strw/corp_home.json",
                "data/strw/orcid.json",
                "data/strw/scopus.json",
            ]

    ## load the Senzing entity resolution results into an `RDFlib`
    ## semantic graph, and serialize the resulting thesaurus as
    ## `thesaurus.ttl` in "Turtle" format
    thes: Thesaurus = Thesaurus()

    thes.parse_er_export(
        datasets,
        export_path = export_path,
        er_path = pathlib.Path("thesaurus.ttl"),
        debug = True,
    )

    thes.load_er_thesaurus(
        er_path = pathlib.Path("thesaurus.ttl"),
    )

    ## serialize `NetworkX` property graph which stores a semantic
    ## layer in node-link format as `sem.json`
    thes.save_sem_layer(pathlib.Path("sem.json"))
