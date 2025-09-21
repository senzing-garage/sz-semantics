#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` to mask PII values in Senzing JSON.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import pathlib

from sz_semantics import Thesaurus


if __name__ == "__main__":
    thes: Thesaurus = Thesaurus()

    ## load the Senzing entity resolution results into an `RDFlib`
    ## semantic graph, and serialize the resulting thesaurus as
    ## `thesaurus.ttl` in "Turtle" format
    thes.parse_er_export(
        [
            "data/acme_biz.json",
            "data/corp_home.json",
            "data/orcid.json",
            "data/scopus.json",
        ],
        export_path = pathlib.Path("data/export.json"),
        er_path = pathlib.Path("thesaurus.ttl"),
        debug = True,
    )

    thes.load_er_thesaurus(
        er_path = pathlib.Path("thesaurus.ttl"),
    )

    ## serialize `NetworkX` property graph which stores a semantic
    ## layer in node-link format as `sem.json`
    thes.save_sem_layer(pathlib.Path("sem.json"))
