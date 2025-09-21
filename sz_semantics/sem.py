#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manage a domain context, using `RDFlib`, `NetworkX`, and related libraries.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

from enum import StrEnum
import json
import logging
import pathlib
import typing

from icecream import ic
from rdflib.namespace import DCTERMS, RDF, ORG, SKOS
import networkx as nx
import rdflib


class SzVocab (StrEnum):
    """
Values for relations in the `sz:` RDF vocabulary.
    """
    COMPOUND_ELEM_OF = "sz:compound_elem_of"
    CO_OCCURS_WITH = "sz:co_occurs_with"
    FOLLOWS_LEXICALLY = "sz:follows_lexically"
    LEMMA_PHRASE = "sz:lemma_phrase"
    WITHIN_CHUNK = "sz:within_chunk"


class NodeKind (StrEnum):
    """
Values for the `kind` property in graph nodes.
    """
    CHUNK = "Chunk"
    ENTITY = "Entity"
    TAXONOMY = "Taxonomy"


class Thesaurus:
    """
Represent the domain context using an _ontology pipeline_ process:
vocabulary, taxonomy, thesaurus, and ontology.
    """
    SZ_BASE: str = "https://github.com/senzing-garage/sz-semantics/wiki/ns#"
    SZ_PREFIX: str = "sz:"


    def __init__ (
        self,
        *,
        domain_path: pathlib.Path = pathlib.Path("domain.ttl"),
        ) -> None:
        """
Constructor.
        """
        self.logger = logging.getLogger(__name__)

        self.use_lemmas: bool = False
        self.known_lemma: typing.List[ str ] = []

        self.taxo_node: typing.Dict[ str, int ] = {}
        self.sem_layer: nx.MultiDiGraph = nx.MultiDiGraph()

        self.rdf_graph: rdflib.Graph = rdflib.Graph()

        self.rdf_graph.parse(
            domain_path.as_posix(),
            format = "turtle",
        )


    def form_concept (
        self,
        fragment: str,
        ) -> rdflib.term.URIRef:
        """
Lookup a `skos:Concept` entity by its IRI.
        """
        iri: str = f"{self.SZ_BASE}{fragment}"
        concept_iri: rdflib.term.URIRef = rdflib.term.URIRef(iri)

        return concept_iri


    def rel_iri (
        self,
        rel: SzVocab,
        ) -> rdflib.term.URIRef:
        """
Accessor to construct a `URIRef` for a relation within the `sz:` vocabulary.
        """
        return rdflib.term.URIRef(
            self.SZ_BASE + rel.value.replace(self.SZ_PREFIX, "")
        )


    def lemmatize (
        self,
        text: str,
        ) -> str:
        """
Mocked method.
        
Subclass and override this method if building a _lexical graph_ using
NLP lemmas as the thesaurus synonyms.
        """
        return text.strip().lower().replace('"', "'")


    def add_lemma (
        self,
        lemma_key: str,
        ) -> bool:
        """
Add a known entity, indexed by its parsed lemma key.
        """
        prev_known: bool = True

        if lemma_key not in self.known_lemma:
            self.known_lemma.append(lemma_key)
            prev_known = False

        return prev_known


    def get_lemma_index (
        self,
        lemma_key: str,
        ) -> int:
        """
Lookup the UID for nodes in the semantic layer, based on a parsed
lemma key for a known entity.
        """
        return self.known_lemma.index(lemma_key)


    def get_first_lemma (
        self,
        concept_iri: rdflib.term.Node,
        ) -> str:
        """
If using NLP lemmas, get the primary lemma for a given `skos:Concept`
entity. Otherwise provide a mocked value.
        """
        if not self.use_lemmas:
            return self.lemmatize(
                next(
                    self.rdf_graph.objects(concept_iri, SKOS.prefLabel)
                ).toPython()  # type: ignore
            )

        lemma_phrase_iri: rdflib.term.URIRef = self.rel_iri(SzVocab.LEMMA_PHRASE)

        return next(
            self.rdf_graph.objects(concept_iri, lemma_phrase_iri)
        ).toPython()  # type: ignore


    def get_ner_labels (
        self,
        ) -> typing.List[ str ]:
        """
Iterate through `skos:Concept` entities to extract the labels used for
zero-shot NER.
        """
        return [
            label.toPython()  # type: ignore
            for concept_iri in self.rdf_graph.subjects(RDF.type, SKOS.Concept)
            for label in self.rdf_graph.objects(concept_iri, SKOS.prefLabel, unique = True)
        ]


    def get_label_map (
        self,
        ) -> typing.Dict[ str, str ]:
        """
Iterate through `skos:Concept` entities to extract a mapping between
NER labels and abbreviated IRIs.
        """
        return {
            label.toPython(): concept_iri.n3(self.rdf_graph.namespace_manager)  # type: ignore
            for concept_iri in self.rdf_graph.subjects(RDF.type, SKOS.Concept)
            for label in self.rdf_graph.objects(concept_iri, SKOS.prefLabel, unique = True)
        }


    def populate_taxo_node (
        self,
        concept_iri: rdflib.term.URIRef,
        ) -> typing.Tuple[ int, str, dict ]:
        """
Populate a `NetworkX` node in the semantic layer from a
`skos:Concept` entity in the RDF taxonomy.
        """
        if not self.use_lemmas:
            # create a mock value for the lemma, to avoid having to
            # build a `spaCy` pipeline for the default case
            lemma_key: str = self.get_first_lemma(concept_iri)
            lemmas: typing.List[ str ] = [ lemma_key ]
        else:
            lemma_phrase_iri: rdflib.term.URIRef = self.rel_iri(SzVocab.LEMMA_PHRASE)

            # scan the `sz:lemma_phrase` triples, collecing their objects
            lemmas = [
                lemma.toPython()  # type: ignore
                for lemma in self.rdf_graph.objects(concept_iri, lemma_phrase_iri)
            ]

            lemma_key = lemmas[0]

        # lookup a unique node ID value for indexing
        self.add_lemma(lemma_key)
        node_id: int = self.get_lemma_index(lemma_key)

        label: str = concept_iri.n3(self.rdf_graph.namespace_manager)
        self.taxo_node[label] = node_id

        text: str = self.rdf_graph.value(
            concept_iri,
            SKOS.definition,
        ).toPython()  # type: ignore

        iri: str = self.rdf_graph.value(
            concept_iri,
            DCTERMS.identifier,
        ).toPython()  # type: ignore

        self.sem_layer.add_node(
            node_id,
            kind = NodeKind.TAXONOMY.value,
            label = label,
            key = lemma_key,
            text = text,
            iri = iri,
            rank = 0.0,
            count = 0,
        )

        # scheduled as relations to get added, once the nodes are in place
        attrs = {
            "lemmas": lemmas,
            "broader": [
                self.get_first_lemma(node)
                for node in self.rdf_graph.objects(concept_iri, SKOS.broader)
            ],
            "narrower": [
                self.get_first_lemma(node)
                for node in self.rdf_graph.objects(concept_iri, SKOS.narrower)
            ],
            "related": [
                self.get_first_lemma(node)
                for node in self.rdf_graph.objects(concept_iri, SKOS.related)
            ],
        }

        return node_id, lemma_key, attrs


    def populate_er_node (
        self,
        er_graph: rdflib.Graph,
        entity_iri: rdflib.term.Node,
        ) -> int:
        """
Populate a semantic layer node from an ER entity.
        """
        if not self.use_lemmas:
            # create a mock value for the lemma, to avoid having to
            # build a `spaCy` pipeline for the default case
            lemma_key: str = self.get_first_lemma(entity_iri)
            lemmas: typing.List[ str ] = [ lemma_key ]
        else:
            lemma_phrase_iri: rdflib.term.URIRef = self.rel_iri(StrwVocab.LEMMA_PHRASE)

            lemmas: typing.List[ str ] = [
                lemma.toPython()  # type: ignore
                for lemma in er_graph.objects(entity_iri, lemma_phrase_iri)
            ]

            lemma_key: str = lemmas[0]

        self.add_lemma(lemma_key)
        node_id: int = self.get_lemma_index(lemma_key)

        label: str = entity_iri.n3(er_graph.namespace_manager)

        text: str = er_graph.value(
            entity_iri,
            SKOS.prefLabel,
        ).toPython()  # type: ignore

        self.sem_layer.add_node(
            node_id,
            kind = NodeKind.ENTITY.value,
            label = label,
            text = text,
            iri = entity_iri,
            rank = 0.0,
            count = 1,
        )

        return node_id


    def seed_sem_layer (
        self,
        ) -> nx.MultiDiGraph():
        """
Iterate through the `skos:Concept` entities, loading them into
the `NetworkX` property graph to initialize a semantic layer.
        """
        node_map: typing.Dict[ str, int ] = {}
        attr_map: typing.Dict[ int, dict ] = {}

        # pass 1: populate nodes for the `skos:Concept` entities into
        # the `NetworkX` property graph
        for concept_iri in self.rdf_graph.subjects(RDF.type, SKOS.Concept):
            node_id, lemma_key, attr = self.populate_taxo_node(concept_iri)
            node_map[lemma_key] = node_id
            attr_map[node_id] = attr

        # pass 2: add edges -- as SKOS semantic relations -- among the
        # populated nodes into `NetworkX`
        for src_id, attr in attr_map.items():
            for rel in [ "broader", "narrower", "related" ]:
                rel_iri: str = f"skos:{rel}"

                for dst_key in attr[rel]:
                    dst_id: int = node_map[dst_key]

                    self.sem_layer.add_edge(
                        src_id,
                        dst_id,
                        key = rel_iri,
                        prob = 1.0,
                    )


    @classmethod
    def scrub_name (
        cls,
        name: str,
        ) -> str:
        """
Scrub disallowed characters from a name going into an RDF language property.
        """
        return name.replace('"', "'").strip()


    def get_name (
        self,
        record_id: str,
        rec_type: str,
        rec: dict,
        org_map: typing.Dict[ str, str ],
        ) -> typing.Tuple[ str, str, typing.List[ str ] ]:
        """
Extract the name and optional employer from a data record.
        """
        name: str = record_id
        employer: str = ""
        urls: typing.List[ str ] = []

        if rec_type == "sz:Organization":
            if "NAMES" in rec:
                names: dict = rec["NAMES"][0]

                if "PRIMARY_NAME_ORG" in names:
                    name = names.get("PRIMARY_NAME_ORG").strip()
                elif "NAME_ORG" in names:
                    name = names.get("NAME_ORG").strip()
                else:
                    log_msg = f"No name item? {names}"
                    self.logger.error(log_msg)

            elif "PRIMARY_NAME_ORG" in rec:
                name = rec.get("PRIMARY_NAME_ORG").strip()

            else:
                log_msg: str = f"No name? {rec}"
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
                name = rec.get("PRIMARY_NAME_FULL").strip()

            elif "PRIMARY_NAME_LAST" in rec:
                name = rec.get("PRIMARY_NAME_LAST").strip()

                if "PRIMARY_NAME_MIDDLE" in rec:
                    name = rec.get("PRIMARY_NAME_MIDDLE").strip() + " " + name

                if "PRIMARY_NAME_FIRST" in rec:
                    name = rec.get("PRIMARY_NAME_FIRST").strip() + " " + name

            elif "NAME_LAST" in rec:
                name = rec.get("NAME_LAST").strip()

                if "NAME_MIDDLE" in rec:
                    name = rec.get("NAME_MIDDLE").strip() + " " + name

                if "NAME_FIRST" in rec:
                    name = rec.get("NAME_FIRST").strip() + " " + name

            elif "PRIMARY_NAME_FIRST" in rec:
                name = rec.get("PRIMARY_NAME_FIRST").strip()

            elif "NATIVE_NAME_FULL" in rec:
                name = rec.get("NATIVE_NAME_FULL").strip()

            else:
                log_msg: str = f"No name? {rec}"
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


    def parse_er_export (  # pylint: disable=R0912,R0913,R0914,R0915
        self,
        datasets: typing.List[ str ],
        *,
        export_path: pathlib.Path = pathlib.Path("data/export.json"),
        er_path: pathlib.Path = pathlib.Path("thesaurus.ttl"),
        encoding: str = "utf-8",
        language: str = "en",
        debug: bool = False,
        ) -> None:
        """
Provide the datasets used in Senzing ER to link entities and load the
metadata for data records as nodes in the resulting graph.

Then parse the Senzing entity resolution (ER) results exported as JSON.
        """
        rdf_list: typing.List[ str ] = [
            """
@prefix sz:    <https://github.com/senzing-garage/sz-semantics/wiki/ns#> .

@prefix dc:    <http://purl.org/dc/terms/> .
@prefix org:   <http://www.w3.org/ns/org#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
            """
        ]

        org_map: typing.Dict[ str, str ] = {}
        parent: typing.Dict[ str, str ] = {}

        # load the data records
        data_records: typing.Dict[ str, dict ] = {}

        for filename in datasets:
            data_path: pathlib.Path = pathlib.Path(filename)

            with open(data_path, encoding = encoding) as fp:
                for line in fp:
                    rec: dict = json.loads(line)
                    record_id: str = self.SZ_PREFIX + rec["DATA_SOURCE"].replace(" ", "_").lower() + "_" + rec["RECORD_ID"]  # pylint: disable=C0301
                    data_records[record_id] = rec

        # parse the JSON export
        with open(export_path, encoding = encoding) as fp:
            for line in fp:
                data: dict = json.loads(line)

                if debug:
                    log_msg: str = f"jsonl: {data}"
                    self.logger.debug(log_msg)

                entity_id: str = self.SZ_PREFIX + str(data["RESOLVED_ENTITY"]["ENTITY_ID"])
                ent_descrip: str = ""
                ent_type: str = ""

                rec_list: typing.List[ dict ] = []
                rel_list: typing.List[ dict ] = []

                for rec in data["RESOLVED_ENTITY"]["RECORDS"]:
                    ent_descrip = rec["ENTITY_DESC"]

                    record_id = rec["RECORD_ID"]
                    data_source: str = rec["DATA_SOURCE"].replace(" ", "_").lower()
                    rec_iri: str = f"{self.SZ_PREFIX}{data_source}_{record_id}"
                    parent[rec_iri] = entity_id

                    pred_iri: str = "skos:exactMatch"

                    rec_list.append({
                        "pred": pred_iri,
                        "obj": rec_iri,
                        "skos:prefLabel": self.scrub_name(rec["ENTITY_DESC"]),
                    })

                for rel in data["RELATED_ENTITIES"]:
                    match_key: str = rel["MATCH_KEY"]
                    match_level: int = rel["MATCH_LEVEL"]
                    match_code: str = rel["MATCH_LEVEL_CODE"]

                    why: str = f"{match_key} {match_level}"
                    pred_iri = "skos:related"

                    if match_code == "POSSIBLY_SAME":
                        pred_iri = "skos:closeMatch"

                    rel_list.append({
                        "pred": pred_iri,
                        "obj": self.SZ_PREFIX + str(rel["ENTITY_ID"]),
                        "skos:definition": why,
                    })

                ent_descrip = self.scrub_name(ent_descrip)

                ent_node: dict = {
                    "iri": entity_id,
                    "skos:prefLabel": ent_descrip,
                }

                if debug:
                    log_msg = f"ent: {ent_node}"
                    self.logger.debug(log_msg)

                rdf_frag: str = f"{entity_id} skos:prefLabel \"{ent_descrip}\"@{language} "

                if self.use_lemmas:
                    lemma_key: str = self.lemmatize(ent_descrip)
                    rdf_frag += f";\n  sz:lemma_phrase \"{lemma_key}\"@{language} "

                if len(data_records) > 0:
                    for rec_node in rec_list:
                        dat_rec: dict = data_records[rec_node["obj"]]
                        ent_type = dat_rec["RECORD_TYPE"]
                        rdf_frag += f';\n  {rec_node["pred"]} {rec_node["obj"]} '

                        if ent_type == "ORGANIZATION":
                            org_map[rec_node["skos:prefLabel"]] = entity_id

                    for rel_node in rel_list:
                        rdf_frag += f';\n  {rel_node["pred"]} {rel_node["obj"]} '

                    rdf_frag += f";\n  rdf:type sz:SzEntity, sz:{ent_type.capitalize()} "
                    rdf_frag += "\n."
                    rdf_list.append(rdf_frag)

        # add nodes representing the data records into the RDF graph
        for record_id, rec in data_records.items():
            rec_type: str = f'sz:{rec["RECORD_TYPE"].capitalize()}'
            name, employer, urls = self.get_name(record_id, rec_type, rec, org_map)

            rdf_frag = f"{record_id} rdf:type sz:DataRecord, {rec_type} "
            rdf_frag += f";\n  skos:prefLabel \"{name}\"@{language} "

            if self.use_lemmas:
                lemma_key = self.lemmatize(name)
                rdf_frag += f";\n  sz:lemma_phrase \"{lemma_key}\"@{language} "

            for url in urls:
                rdf_frag += f";\n  dc:identifier <{url}> "

            rdf_frag += "\n."
            rdf_list.append(rdf_frag)

            if len(employer) > 0:
                rdf_frag = f"{parent[record_id]} org:memberOf {employer} ."
                rdf_list.append(rdf_frag)

        # serialize the generated RDF file
        with open(er_path, "w", encoding = encoding) as fp:
            fp.write("\n".join(rdf_list))

        # load the RDF graph and initialize the semantic layer
        self.rdf_graph.parse(
            er_path.as_posix(),
            format = "turtle",
        )

        self.seed_sem_layer()


    def load_er_thesaurus (
        self,
        er_path: pathlib.Path = pathlib.Path("thesaurus.ttl"),
        ) -> None:
        """
Iterate through the _entity resolution_ results, adding a domain-specific
thesaurus of entities and relations into the semantic layer.

Be sure to call `parse_er_export()` beforehand.
        """
        # load the ER triples into their own graph, to extract and
        # link the known synonyms in the thesaurus
        node_map: typing.Dict[ str, int ] = {}
        er_graph: rdflib.Graph = rdflib.Graph()

        er_graph.parse(
            er_path.as_posix(),
            format = "turtle",
        )

        # first iterate through the data records, loading lemma keys
        # and populating nodes in the semantic layer
        for entity_iri in er_graph.subjects(RDF.type, self.form_concept("DataRecord")):
            node_id = self.populate_er_node(er_graph, entity_iri)
            node_map[entity_iri.n3(er_graph.namespace_manager)] = node_id

        # now iterate through the entities, overriding any prior lemma
        # keys from data records
        for entity_iri in er_graph.subjects(RDF.type, self.form_concept("SzEntity")):
            node_id = self.populate_er_node(er_graph, entity_iri)
            node_map[entity_iri.n3(er_graph.namespace_manager)] = node_id

        # then add SKOS relations (thesaurus synonyms and taxonymy)
        # as edges in the semantic layer
        for entity_iri in er_graph.subjects(RDF.type, self.form_concept("SzEntity")):
            for sem_rel in [ SKOS.related, SKOS.closeMatch, SKOS.exactMatch, ORG.memberOf ]:
                for obj in er_graph.objects(entity_iri, sem_rel):
                    src_id: int = node_map[entity_iri.n3(er_graph.namespace_manager)]
                    dst_id: int = node_map[obj.n3(er_graph.namespace_manager)]

                    if src_id != dst_id:
                        rel_iri: str = sem_rel.n3(er_graph.namespace_manager)
                        prob: float = 0.5

                        if rel_iri in [ "skos:exactMatch", "org:memberOf" ]:
                            prob = 1.0

                        self.sem_layer.add_edge(
                            src_id,
                            dst_id,
                            key = rel_iri,
                            prob = prob,
                        )

        # also link entities to their taxonomy nodes
        for taxo_iri in [ self.form_concept("Organization"), self.form_concept("Person") ]:
            for entity_iri in er_graph.subjects(RDF.type, taxo_iri):
                node_id = node_map[entity_iri.n3(er_graph.namespace_manager)]
                taxo_node_id: int = self.taxo_node[taxo_iri.n3(self.rdf_graph.namespace_manager)]

                self.sem_layer.add_edge(
                    node_id,
                    taxo_node_id,
                    key = "RDF:type",
                    weight = 0.0
                )

        # finally, load ER triples into the semantic layer
        self.rdf_graph.parse(
            er_path.as_posix(),
            format = "turtle",
        )


    def save_sem_layer (
        self,
        kg_path: pathlib.Path,
        *,
        encoding: str = "utf-8",
        ) -> None:
        """
Serialize the constructed KG as a JSON file represented in the
_node-link_ data format.

Aternatively this could be stored in a graph database.
        """
        with kg_path.open("w", encoding = encoding) as fp:
            fp.write(
                json.dumps(
                    nx.node_link_data(
                        self.sem_layer,
                        edges = "edges",
                    ),
                    indent = 2,
                    sort_keys = True,
                )
            )
