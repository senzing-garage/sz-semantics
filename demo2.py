#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` for Semantic Represenation of Senzing ER results.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import io
import logging
import pathlib

from sz_semantics import Thesaurus


if __name__ == "__main__":
    logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(level = logging.WARNING) # DEBUG

    # initialize a thesaurus and load the Senzing taxonomy
    thesaurus: Thesaurus = Thesaurus()
    thesaurus.load_source(Thesaurus.DOMAIN_TTL) # "domain.ttl"

    # write the preamble of RDF vocabular prefixes
    thesaurus_path: pathlib.Path = pathlib.Path("the.ttl")
    fp_rdf: io.TextIOWrapper = thesaurus_path.open("w", encoding = "utf-8")  # pylint: disable=R1732
    fp_rdf.write(Thesaurus.RDF_PREAMBLE)

    # load the Senzing ER exported JSON, and generate RDF fragments
    # for representing each Sezning entity -- this could be made
    # concurrent/parallel with `asynchio`
    export_path: pathlib.Path = pathlib.Path("data/truth/export.json")

    with open(export_path, "r", encoding = "utf-8") as fp_json:
        for line in fp_json:
            for rdf_frag in thesaurus.parse_iter(line, language = "en"):
                fp_rdf.write(rdf_frag)
                fp_rdf.write("\n")

    thesaurus.load_source(thesaurus_path, format = "turtle")

    # serialize the Senzing taxonomy + generated thesaurus
    sem_layer_path: pathlib.Path = pathlib.Path("sem.ttl")
    thesaurus.save_source(sem_layer_path, format = "turtle")
