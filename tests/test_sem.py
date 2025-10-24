#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
unit tests:

  * Semantic Represenation

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import os
import pathlib
import tempfile

from rdflib import Namespace  # pylint: disable=W0611
from rdflib.plugins.sparql.processor import SPARQLResult

from sz_semantics import Thesaurus


def test_sem (
    *,
    debug: bool = False,  # pylint: disable=W0613
    ) -> None:
    """
Verify that the Senzing ER results are represented correctly in RDF.
    """
    exp_res: set = {
        "sz:customers_1001",
        "sz:customers_1002",
        "sz:customers_1003",
        "sz:customers_1004",
    }

    # initialize a thesaurus and load the Senzing taxonomy
    thesaurus: Thesaurus = Thesaurus()
    thesaurus.load_source(Thesaurus.DOMAIN_TTL) # "domain.ttl"

    # write the preamble of RDF vocabular prefixes
    fp_rdf: tempfile._TemporaryFileWrapper = tempfile.NamedTemporaryFile(  # pylint: disable=R1732
        mode = "w",
        encoding = "utf-8",
        delete = False,
    )

    fp_rdf.write(Thesaurus.RDF_PREAMBLE)

    # load the Senzing ER exported JSON, and generate RDF fragments
    # for representing each Sezning entity
    export_path: pathlib.Path = pathlib.Path("data/truth/export.json")

    with open(export_path, "r", encoding = "utf-8") as fp_json:
        for line in fp_json:
            for rdf_frag in thesaurus.parse_iter(line, language = "en"):
                fp_rdf.write(rdf_frag)
                fp_rdf.write("\n")

    thesaurus.load_source(fp_rdf.name, format = "turtle")

    # map the entities to data records
    query: str = """
SELECT ?rec
WHERE {
  sz:1 prov:wasDerivedFrom ?rec .    
}"""

    qres: SPARQLResult = thesaurus.rdf_graph.query(query)  # type: ignore

    obs_res: set = {
        str(uri.n3(thesaurus.rdf_graph.namespace_manager))
        for row in qres
        for uri in row  # type: ignore
    }

    if debug:
        print(obs_res)

    # test for expected results
    assert exp_res == obs_res

    # delete the temporary file
    fp_rdf.close()
    os.remove(fp_rdf.name)


if __name__ == "__main__":
    test_sem(debug = True)
