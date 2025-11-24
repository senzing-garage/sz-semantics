#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
unit tests:

  * Semantic Representation

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import os
import pathlib
import tempfile

from rdflib import Namespace  # pylint: disable=W0611
from rdflib.plugins.sparql.processor import SPARQLResult

from sz_semantics import Thesaurus


def test_sem(
    *,
    debug: bool = False,  # pylint: disable=W0613
) -> None:
    """
    Verify that the Senzing ER results are represented correctly in RDF.
    """
    exp_res: set = {
        "sz:ds_customers_1001",
        "sz:ds_customers_1002",
        "sz:ds_customers_1003",
        "sz:ds_customers_1004",
    }

    # point to the correct directory for input files
    base_dir: pathlib.Path = pathlib.Path(__file__).parent.parent.resolve()

    # initialize a thesaurus and load the Senzing taxonomy
    domain_path: pathlib.Path = base_dir / "domain.ttl"

    thesaurus: Thesaurus = Thesaurus()
    thesaurus.load_source(domain_path)

    # write the preamble of RDF vocabulary prefixes
    fp_rdf: tempfile._TemporaryFileWrapper = (
        tempfile.NamedTemporaryFile(  # pylint: disable=R1732
            mode="w",
            encoding="utf-8",
            delete=False,
        )
    )

    fp_rdf.write(Thesaurus.RDF_PREAMBLE)

    # load the Senzing ER exported JSON, and generate RDF fragments
    # for representing each Senzing entity
    export_path: pathlib.Path = base_dir / "data/truth/export.json"

    with open(export_path, "r", encoding="utf-8") as fp_json:
        for line in fp_json:
            for rdf_frag in thesaurus.parse_iter(line, language="en"):
                fp_rdf.write(rdf_frag)
                fp_rdf.write("\n")

    thesaurus.load_source(fp_rdf.name, format="turtle")

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
    test_sem(debug=True)
