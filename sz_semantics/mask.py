#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Means of masking PII in JSON from the Senzing SDK.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

from collections import Counter
import json
import logging
import pathlib
import re
import typing

from .util import KeyValueStore


class Mask:
    """
Mask the PII values within Senzing output with tokens, which can be
substituted back later.
    """
    PAT_KEY_PAIR: re.Pattern = re.compile(r"^([\w\_\-]+)\:\s+(.*)$")
    PAT_TOKEN: re.Pattern = re.compile(r"([A-Z_]+_\d+)")

    KNOWN_KEYS: set[ str ] = {
        "AMOUNT",
        "CANDIDATE_CAP_REACHED",
        "CANDIDATE_FEAT_USAGE_TYPE",
        "CATEGORY",
        "DATE",
        "ENTITY_ID",
        "ENTITY_TYPE",
        "ERRULE_CODE",
        "FIRST_SEEN_DT",
        "FTYPE_CODE",
        "INBOUND_FEAT_USAGE_TYPE",
        "INBOUND_VIRTUAL_ENTITY_ID",
        "IS_AMBIGUOUS",
        "IS_DISCLOSED",
        "LAST_SEEN_DT",
        "MATCH_KEY",
        "MATCH_LEVEL",
        "MATCH_LEVEL_CODE",
        "RECORD_TYPE",
        "RESULT_VIRTUAL_ENTITY_ID",
        "SCORE_BEHAVIOR",
        "SCORE_BUCKET",
        "SCORING_CAP_REACHED",
        "SOURCE",
        "STATUS",
        "SUPPRESSED",
        "TOKEN",
        "USAGE_TYPE",
        "USED_FOR_CAND",
        "USED_FOR_SCORING",
        "VIRTUAL_ENTITY_ID",
        "WHY_ERRULE_CODE",
        "WHY_KEY",
    }

    MASKED_KEYS: set[ str ] = {
        "ACCT_NUM",
        "CANDIDATE_FEAT_DESC",
        "DATA_SOURCE",
        "DOB",
        "DRLIC",
        "EMAIL",
        "ENTITY_DESC",
        "ENTITY_KEY",
        "ENTITY_NAME",
        "FEAT_DESC",
        "HOME",
        "INBOUND_FEAT_DESC",
        "ISSUING_BANK",
        "MAILING",
        "MOBILE",
        "PRIMARY",
        "RECORD_ID",
    }


    def __init__ (
        self,
        *,
        kv_store: KeyValueStore = KeyValueStore(),
        ) -> None:
        """
Constructor.

Override `KeyValueStore` to replace the Python built-in `dict` for
larger scale such as [`rocksdict`](https://github.com/rocksdict/rocksdict).

Add values to `KNOWN_KEYS` and `MASKED_KEYS` as needed for
a given use case.
        """
        self.logger = logging.getLogger(__name__)
        self.key_count: Counter = Counter()

        self.tokens: dict[ str, str ] = kv_store.allocate()


    def serialize_json (
        self,
        data: list | dict,
        out_file: pathlib.Path,
        *,
        encoding: str = "utf-8",
        ) -> None:
        """
Serialize a data structure from JSON to a text file in pretty-print
format.
        """
        with open(out_file, "w", encoding = encoding) as fp:
            fp.write(json.dumps(data, indent = 2))
            fp.write("\n")


    def unmask_text (
        self,
        text: str,
        *,
        debug: bool = False,
        ) -> str:
        """
Substitute the original PII values for masked tokens within a text.
        """
        last_head: int = 0
        collected: list = []

        for hit in self.PAT_TOKEN.finditer(text):
            key: str = hit.group(0)
            pii: str | None = self.tokens.get(key)

            if debug:
                log_msg: str = f"{key} {pii}"
                self.logger.debug(log_msg)

            if pii is not None:
                head: int = hit.start()
                tail: int = hit.end()

                if debug:
                    log_msg = f" => {key} {head} {tail} {pii}"
                    self.logger.debug(log_msg)

                collected.append(text[last_head:head])
                collected.append(pii)
                last_head = tail

        collected.append(text[last_head:])
        return "".join(collected)


    def mask_value (
        self,
        key: str,
        elem: typing.Any,
        ) -> str:
        """
Mask a one PII value represented as a key/value pair.
        """
        if elem in self.tokens.values():
            # has this value been previously seen?
            elem_index: int = list(self.tokens.values()).index(elem)
            found_key: str = list(self.tokens.keys())[elem_index]

            if found_key.startswith(key):
                return found_key

        # nope, it's a new value
        self.key_count[key] += 1
        masked_elem: str = f"{key}_{self.key_count[key]}".upper()
        self.tokens[masked_elem] = elem

        return masked_elem


    def dive_key_pair (
        self,
        key: str,
        elem: typing.Any,
        *,
        debug: bool = False,
        ) -> list:
        """
Handle a key pair for a literal value.
        """
        if isinstance(elem, list):
            return [ key, self.mask_data(elem, debug = debug) ]

        if isinstance(elem, dict):
            return [ key, self.mask_data(elem, debug = debug) ]

        if key in self.MASKED_KEYS:
            if debug:
                log_msg: str = f"MASKED: {key} {elem}"
                self.logger.debug(log_msg)

            masked_elem: str = self.mask_value(key, elem)

            if elem == masked_elem:
                log_msg = f"NOT MASKED: {elem} == {masked_elem}"
                self.logger.error(log_msg)

            return [ key, masked_elem ]

        if isinstance(elem, int) or key in self.KNOWN_KEYS:
            return [ key, elem ]

        if isinstance(elem, str):
            log_msg = f"UNKNOWN key: {key} {elem}"
            logging.warning(log_msg)

            masked_elem = self.mask_value(key, elem)

            if elem == masked_elem:
                log_msg = f"NOT MASKED: {elem} == {masked_elem}"
                self.logger.error(log_msg)

            return [ key, masked_elem ]

        # otherwise pass through
        if debug:
            log_msg = f"{key} {type(elem)}"
            self.logger.debug(log_msg)

        return self.mask_data(elem, debug = debug)  # type: ignore


    def mask_data (
        self,
        data: list | dict,
        *,
        debug: bool = False,
        ) -> list | dict:
        """
Recursive descent through JSON data structures (lists, dictionaries)
until reaching kev/value pairs or a collection of string literals.
        """
        if debug:
            rep: str = f"\n{str(type(data))}: {str(data)[:50]} ..."
            self.logger.debug(rep)

        if isinstance(data, list):
            return [
                self.mask_data(elem, debug = debug)
                for elem in data
            ]

        if isinstance(data, dict):
            dict_items: dict = {}

            for key, elem in data.items():
                pair: list = self.dive_key_pair(key, elem, debug = debug)
                dict_items[pair[0]] = pair[1]

            return dict_items

        if isinstance(data, str):
            hit: re.Match | None = self.PAT_KEY_PAIR.match(data)

            if hit is not None:
                key = hit.group(1)
                elem = hit.group(2)
                pair = self.dive_key_pair(key, elem, debug = debug)
                result: str = f"{pair[0]}: {pair[1]}"

                return result

        if isinstance(data, int):
            return data

        # a more serious edge case, since we should already have
        # full coverage on the possible data types from eleemnts
        # of deserialized JSON
        log_msg = f"Unknown data type: {type(data)}"
        self.logger.error(log_msg)
        return data
