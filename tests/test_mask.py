#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
unit tests:

  * Mask

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json
import typing

from sz_semantics import Mask


def test_mask(
    *,
    debug: bool = False,  # pylint: disable=W0613
) -> None:
    """
    Verify that the mask/unmask roundtrip protects and preserves the
    PII values correctly.
    """
    exp_data: dict[str, typing.Any] = {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": 1,
            "ENTITY_NAME": "Robert Smith",
            "IDENTIFIER_DATA": ["EMAIL: bsmith@work.com"],
            "ADDRESS_DATA": ["HOME: 1515 Adela Ln Las Vegas NV 89132"],
        },
    }

    exp_text: str = (
        """
        {"RESOLVED_ENTITY": {"ADDRESS_DATA": ["HOME: HOME_1"], "ENTITY_ID": 1, "ENTITY_NAME": "ENTITY_NAME_1", "IDENTIFIER_DATA": ["EMAIL: EMAIL_1"]}}
    """.strip()
    )  # pylint: disable=C0301

    sz_mask: Mask = Mask()
    masked_data: dict = sz_mask.mask_data(exp_data)  # type: ignore

    obs_text: str = json.dumps(masked_data, sort_keys=True)
    assert exp_text == obs_text

    obs_data: dict[str, typing.Any] = json.loads(sz_mask.unmask_text(obs_text))
    assert sorted(exp_data.items()) == sorted(obs_data.items())


if __name__ == "__main__":
    test_mask(debug=True)
