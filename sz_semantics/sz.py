#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A client for Senzing SDK via a gRPC server, which simplifies SDK calls
and makes its use feel a bit more "Pythonic" in practice.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json
import logging
import pathlib

from senzing import szengineflags, szerror
from senzing_grpc import SzAbstractFactoryGrpc, SzConfigManagerGrpc, SzDiagnosticGrpc, SzEngineGrpc, SzConfigGrpc, SzProductGrpc  # type: ignore  # pylint: disable=C0301
import grpc


class SzClient:
    """
Handling typical Senzing SDK interactions via a gRPC server.
    """

    def __init__ (
        self,
        config: dict,
        data_sources: dict,
        *,
        debug: bool = False,
        ) -> None:
        """
Constructor.
        """
        self.logger: logging.Logger = logging.getLogger(__name__)

        grpc_channel: grpc.Channel = grpc.insecure_channel(config["sz"]["grpc_server"])
        sz_abstract_factory: SzAbstractFactoryGrpc = SzAbstractFactoryGrpc(grpc_channel)

        if debug:
            sz_product: SzProductGrpc = sz_abstract_factory.create_product()
            version_json: str = json.loads(sz_product.get_version())

            log_msg: str = f"version: {json.dumps(version_json)}"
            self.logger.debug(log_msg)

        sz_configmanager: SzConfigManagerGrpc = sz_abstract_factory.create_configmanager()

        self.sz_diagnostic: SzDiagnosticGrpc = sz_abstract_factory.create_diagnostic()
        self.sz_engine: SzEngineGrpc = sz_abstract_factory.create_engine()

        # register the datasets
        config_id: int = sz_configmanager.get_default_config_id()
        sz_config: SzConfigGrpc = sz_configmanager.create_config_from_config_id(config_id)

        for dataset in data_sources.keys():
            try:
                sz_config.register_data_source(dataset)

                if debug:
                    log_msg = f"register: {dataset}"
                    self.logger.debug(log_msg)
            except (grpc.RpcError, szerror.SzError):
                log_msg = "each data source only needs to be registered once"
                self.logger.info(log_msg)

        # replace the default config with the updated version
        # which has the datasets registered
        new_config_id: int = sz_configmanager.register_config(
            sz_config.export(),
            "add datasets",
        )

        sz_configmanager.replace_default_config_id(config_id, new_config_id)
        sz_abstract_factory.reinitialize(new_config_id)


    def entity_resolution (  # pylint: disable=R0914
        self,
        data_sources: dict,
        *,
        debug: bool = False,
        ) -> dict:
        """
Load datasets into Senzing and run entity resolution, returning a
dictionary of the resolved entities.
        """
        affected_entities: set = set()

        for dataset in data_sources.values():
            data_path: pathlib.Path = pathlib.Path(dataset)

            for line in data_path.open(encoding = "utf-8"):  # pylint: disable=R1732
                dat: dict = json.loads(line.strip())

                if debug:
                    log_msg: str = f"entity: {dat}"
                    self.logger.debug(log_msg)

                rec_info: str = self.sz_engine.add_record(
                    dat["DATA_SOURCE"],
                    dat["RECORD_ID"],
                    dat,
                    szengineflags.SzEngineFlags.SZ_WITH_INFO,
                )

                if debug:
                    log_msg = f"load: {rec_info}"
                    self.logger.debug(log_msg)

                info: dict = json.loads(rec_info)

                affected_entities.update(
                    [ entity["ENTITY_ID"] for entity in info["AFFECTED_ENTITIES"] ]
                )

        # handle "REDO"
        while True:
            redo_record: str = self.sz_engine.get_redo_record()

            if not redo_record:
                break

            rec_info = self.sz_engine.process_redo_record(
                redo_record,
                flags = szengineflags.SzEngineFlags.SZ_WITH_INFO,
            )

            info = json.loads(rec_info)

            if debug:
                log_msg = f"redo: {rec_info}"
                self.logger.debug(log_msg)

            affected_entities.update(
                [ entity["ENTITY_ID"] for entity in info["AFFECTED_ENTITIES"] ]
            )

        # enumerate the resolved entities
        entity_to_record: dict = {}

        for entity_id in affected_entities:
            try:
                sz_json: str = self.sz_engine.get_entity_by_entity_id(entity_id)

                if debug:
                    log_msg = f"{sz_json}"
                    self.logger.debug(log_msg)

                dat = json.loads(sz_json)
                rec_list: list = dat["RESOLVED_ENTITY"]["RECORDS"]

                entity_to_record[entity_id] = {
                    "name": dat["RESOLVED_ENTITY"]["ENTITY_NAME"],
                    "records": [ rec_list[i]["RECORD_ID"] for i in range(len(rec_list)) ],
                }

            except szerror.SzError:
                # this entity has effectively been removed
                entity_to_record[entity_id] = {
                    "name": None
                }

        ent_ref: dict = {}

        for entity_id, ent in entity_to_record.items():
            name: str | None = ent.get("name")

            if name is not None:
                label: str = f"{name} ({entity_id})"

                ent_ref[label] = {
                    "entity_id": int(entity_id),
                    "name": name,
                    "records": ent.get("records"),
                }

        return ent_ref


    def get_entity (
        self,
        entity_id: int,
        ) -> str:
        """
Accessor to get a JSON description for a given entity ID.
        """
        return self.sz_engine.get_entity_by_entity_id(entity_id)
