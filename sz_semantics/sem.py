#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manage the computable semantics of a domain context, based on using
`RDFlib` and related libraries.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

from collections import Counter
import json
import logging
import pathlib
import typing

from rdflib import Namespace  # pylint: disable=W0611
from rdflib.namespace import DC, DCAT, PROV, RDF, SKOS
import rdflib

from .util import KeyValueStore
from .namespace import SZ


class Thesaurus:
    """
Represent the domain context using an _ontology pipeline_ process:
vocabulary, taxonomy, thesaurus, and ontology.
    """
    SZ_BASE: str = "https://github.com/senzing-garage/sz-semantics/wiki/ns#"
    SZ_PREFIX: str = "sz:"

    DOMAIN_TTL: str = "https://raw.githubusercontent.com/senzing-garage/sz-semantics/refs/heads/main/domain.ttl"  # pylint: disable=C0301

    RDF_PREAMBLE: str = """
@prefix sz:    <https://github.com/senzing-garage/sz-semantics/wiki/ns#> .

@prefix bods:  <https://vocab.openownership.org/terms#> .
@prefix dc:    <http://purl.org/dc/elements/1.1/> .
@prefix dcat:  <http://www.w3.org/ns/dcat#> .
@prefix ftm:   <https://schema.followthemoney.tech/#> .
@prefix prov:  <http://www.w3.org/ns/prov#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix wco:   <https://id.oclc.org/worldcat/ontology/> .
@prefix wd:    <http://www.wikidata.org/entity/> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
        """.lstrip()


    def __init__ (
        self,
        *,
        kv_store: KeyValueStore = KeyValueStore(),
        ) -> None:
        """
Constructor.

This expects the `load_source()` method will be used to load the taxonomy
directly after constructing an instance.

Note: override `KeyValueStore` to replace the Python built-in `dict` for
larger scale such as [`rocksdict`](https://github.com/rocksdict/rocksdict).
        """
        self.logger = logging.getLogger(__name__)
        self.kv_store: KeyValueStore = kv_store

        self.rdf_graph: rdflib.Graph = rdflib.Graph(bind_namespaces = "rdflib")
        self.rdf_graph.bind("dc", DC)
        self.rdf_graph.bind("dcat", DCAT)
        self.rdf_graph.bind("prov", PROV)
        self.rdf_graph.bind("skos", SKOS)
        self.rdf_graph.bind("sz", SZ)

        ## `node_map` maps from IRI (in N3 prefix mode) to node IDs
        self.node_map: dict[ str, int ] = self.kv_store.allocate()


    def load_source (
        self,
        source: typing.Any,
        *,
        format: str = "turtle",  # pylint: disable=W0622
        ) -> None:
        """
Load triples from a data source.
        """
        self.rdf_graph.parse(
            source,
            format = format,
        )


    def save_source (
        self,
        rdf_path: pathlib.Path,
        *,
        format: str = "turtle",  # pylint: disable=W0622
        encoding: str = "utf-8",
        ) -> None:
        """
Serialize triples to a file.
        """
        with open(rdf_path, "w", encoding = encoding) as fp:
            fp.write(
                self.rdf_graph.serialize(
                    format = format,
                )
            )


    def n3 (
        self,
        uri: rdflib.term.URIRef,
        ) -> str:
        """
Normalize IRI prefixes to N3 "Turtle" format.
        """
        return uri.n3(self.rdf_graph.namespace_manager)


    def get_ner_labels (
        self,
        ) -> list[ str ]:
        """
Accessor: iterate through `skos:Concept` entities to extract labels
used for zero-shot NER such as the `GLiNER` library.
        """
        return [
            label.toPython()  # type: ignore
            for concept_iri in self.rdf_graph.subjects(RDF.type, SKOS.Concept)
            for label in self.rdf_graph.objects(concept_iri, SKOS.prefLabel, unique = True)
        ]


    def get_label_map (
        self,
        ) -> dict[ str, str ]:
        """
Accessor: iterate through `skos:Concept` entities to extract a mapping
between NER labels and abbreviated IRIs.

Used for _entity linking_ when using zero-shot NER such as the `GLiNER`
library.
        """
        return {
            label.toPython(): self.n3(concept_iri)  # type: ignore
            for concept_iri in self.rdf_graph.subjects(RDF.type, SKOS.Concept)
            for label in self.rdf_graph.objects(concept_iri, SKOS.prefLabel, unique = True)
        }


    ######################################################################
    ## parse Senzing JSON

    @classmethod
    def scrub_name (
        cls,
        name: str,
        ) -> str:
        """
Scrub disallowed characters from a name going into an RDF language property.
        """
        return name.replace('"', "'").strip()


    def parse_iter (
        self,
        data: dict | list | str,
        *,
        language: str = "en",
        debug: bool = False,
        ) -> typing.Iterator[ str ]:
        """
Handle the different formats for JSON responses from the Senzing SDK
(dictionary, list, or JSONL string) then generate RDF representation
for each entity.
        """
        if isinstance(data, dict):
            yield self._parse_entity(
                data,
                language = language,
                debug = debug,
            )

        elif isinstance(data, list):
            for data_item in data:
                if "RESOLVED_ENTITY" in data_item:
                    yield self._parse_entity(
                        data_item,
                        language = language,
                        debug = debug,
                    )

        elif isinstance(data, str):
            yield self._parse_entity(
                json.loads(data),
                language = language,
                debug = debug,
            )


    def _parse_entity (  # pylint: disable=R0913,R0914,R0915
        self,
        data: dict,
        *,
        language: str = "en",
        debug: bool = False,
        ) -> str:
        """
Transform a Senzing entity, parsed from JSON, into RDF representation.
        """
        if debug:
            log_msg: str = f"jsonl: {data}"
            self.logger.debug(log_msg)

        # parse the resolved data records
        res_ent: dict = data["RESOLVED_ENTITY"]
        entity_id: str = self.SZ_PREFIX + str(res_ent["ENTITY_ID"])
        ent_type: str = ""

        rdf_frag: str = ""
        top_names: Counter = Counter()

        for rec in res_ent["RECORDS"]:
            match_key: str = rec["MATCH_KEY"]
            match_level: int = rec["MATCH_LEVEL"]

            if match_key == "":
                match_key = "INITIAL"

            src_id: str = rec["DATA_SOURCE"].replace(" ", "_").lower()
            src_iri: str = f"{self.SZ_PREFIX}{src_id}"

            rec_id: str = rec["RECORD_ID"]
            rec_iri: str = f"{src_iri}_{rec_id}"

            if "ENTITY_TYPE" in rec and len(ent_type) < 1:
                ent_type = rec["ENTITY_TYPE"]

            rec_name: str = self.scrub_name(rec["ENTITY_DESC"])
            top_names[rec_name] += 1

            # represent the entity <=> data record relationship using
            # a blank node, to capture the match reason
            rdf_frag += f"\n[] {self.n3(RDF.subject)} {entity_id} ;"
            rdf_frag += f"\n {self.n3(RDF.predicate)} {self.n3(SKOS.exactMatch)} ;"
            rdf_frag += f"\n {self.n3(RDF.object)} {rec_iri} ;"
            rdf_frag += f"\n {self.n3(SZ.match_key)} \"{match_key}\" ;"
            rdf_frag += f"\n {self.n3(SZ.match_level)} {match_level} ."

            rdf_frag += f"\n {entity_id} {self.n3(PROV.wasDerivedFrom)} {rec_iri} ."

            # represent the data record
            rdf_frag += f"\n{rec_iri} {self.n3(RDF.type)} {self.n3(SZ.DataRecord)} ;"
            rdf_frag += f"\n {self.n3(SKOS.prefLabel)} \"{rec_name}\"@{language} ;"
            rdf_frag += f"\n {self.n3(DC.identifier)} \"{rec_id}\" ;"
            rdf_frag += f"\n {self.n3(PROV.wasQuotedFrom)} {src_iri} ."

            # represent the data source -
            # duplicates get ignored during RDF parse
            rdf_frag += f"\n{src_iri} {self.n3(RDF.type)} {self.n3(DCAT.Dataset)} ;"
            rdf_frag += f"\n {self.n3(DC.identifier)} \"{src_id}\" ."

        # parse the related entities
        for rel in data["RELATED_ENTITIES"]:
            match_key = rel["MATCH_KEY"]
            match_level = rel["MATCH_LEVEL"]
            match_code = rel["MATCH_LEVEL_CODE"]

            rel_iri: str = self.SZ_PREFIX + str(rel["ENTITY_ID"])
            rel_pred: str = self.n3(SKOS.related)

            if match_code == "POSSIBLY_SAME":
                rel_pred = self.n3(SKOS.closeMatch)

            # represent the entity <=> related entty relationship
            # using a blank node, to capture the match reason
            rdf_frag += f"\n[] {self.n3(RDF.subject)} {entity_id} ;"
            rdf_frag += f"\n {self.n3(RDF.predicate)} {rel_pred} ;"
            rdf_frag += f"\n {self.n3(RDF.object)} {rel_iri} ;"
            rdf_frag += f"\n {self.n3(SZ.match_key)} \"{match_key}\" ;"
            rdf_frag += f"\n {self.n3(SZ.match_level)} {match_level} ."

        # generate the RDF represenation for this entity
        if ent_type in [ "GENERIC" ]:
            ent_type = "Person"

        rdf_frag += f"\n{entity_id} {self.n3(RDF.type)} sz:{ent_type.capitalize()} ."

        if len(top_names) > 0:
            ent_descrip: str = top_names.most_common(1)[0][0]
            rdf_frag += f"\n{entity_id} {self.n3(SKOS.prefLabel)} \"{ent_descrip}\"@{language} ."

        return rdf_frag


    ######################################################################
    ## Deprecated: parse the semantics of Senzing ER JSON

    def get_name (  # pylint: disable=R0912,R0915
        self,
        record_id: str,
        rec_type: str,
        rec: dict,
        org_map: dict[ str, str ],
        ) -> tuple[ str, str, list[ str ] ]:
        """
Extract the name and optional employer from a data record.
        """
        name: str = record_id
        employer: str = ""
        urls: list[ str ] = []

        if rec_type == self.n3(SZ.Organization):
            if "NAMES" in rec:
                names: dict = rec["NAMES"][0]

                if "PRIMARY_NAME_ORG" in names:
                    name = names.get("PRIMARY_NAME_ORG").strip()  # type: ignore
                elif "NAME_ORG" in names:
                    name = names.get("NAME_ORG").strip()  # type: ignore
                else:
                    log_msg = f"No name item? {names}"
                    self.logger.error(log_msg)

            elif "PRIMARY_NAME_ORG" in rec:
                name = rec.get("PRIMARY_NAME_ORG").strip()  # type: ignore

            else:
                log_msg = f"No name? {rec}"
                self.logger.warning(log_msg)

            # other metadata
            if "LINKS" in rec:
                for url_dict in rec["LINKS"]:
                    for url in url_dict.values():
                        urls.append(url)

            if "WEBSITE_ADDRESS" in rec:
                urls.append(rec["WEBSITE_ADDRESS"])

        else:
            if "PRIMARY_NAME_FULL" in rec:
                name = rec.get("PRIMARY_NAME_FULL").strip()  # type: ignore

            elif "PRIMARY_NAME_LAST" in rec:
                name = rec.get("PRIMARY_NAME_LAST").strip()  # type: ignore

                if "PRIMARY_NAME_MIDDLE" in rec:
                    name = rec.get("PRIMARY_NAME_MIDDLE").strip() + " " + name  # type: ignore

                if "PRIMARY_NAME_FIRST" in rec:
                    name = rec.get("PRIMARY_NAME_FIRST").strip() + " " + name  # type: ignore

            elif "NAME_LAST" in rec:
                name = rec.get("NAME_LAST").strip()  # type: ignore

                if "NAME_MIDDLE" in rec:
                    name = rec.get("NAME_MIDDLE").strip() + " " + name  # type: ignore

                if "NAME_FIRST" in rec:
                    name = rec.get("NAME_FIRST").strip() + " " + name  # type: ignore

            elif "PRIMARY_NAME_FIRST" in rec:
                name = rec.get("PRIMARY_NAME_FIRST").strip()  # type: ignore

            elif "NATIVE_NAME_FULL" in rec:
                name = rec.get("NATIVE_NAME_FULL").strip()  # type: ignore

            else:
                log_msg = f"No name? {rec}"
                self.logger.warning(log_msg)

            # other metadata
            if "SOURCE_LINKS" in rec:
                for url_dict in rec["SOURCE_LINKS"]:
                    for url in url_dict.values():
                        urls.append(url)

            if "EMPLOYER_NAME" in rec:
                org_name: str = self.scrub_name(rec["EMPLOYER_NAME"])

                if org_name in org_map:
                    employer = org_map.get(org_name)  # type: ignore

        return self.scrub_name(name), employer, urls
