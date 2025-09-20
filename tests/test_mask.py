#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
unit tests:

  * SzMask

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json

from sz_semantics import SzMask


def test_mask (
    *,
    debug: bool = False,
    ) -> None:
    """
Check the the mask/unmask roundtrip protects and preserves the
PII values correctly.
    """
    exp_data: dict = {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": 1,
            "ENTITY_NAME": "Robert Smith",
            "IDENTIFIER_DATA": [
                "EMAIL: bsmith@work.com"
            ],
            "ADDRESS_DATA": [
                "HOME: 1515 Adela Ln Las Vegas NV 89132"
            ],
        },
    }

    sz_mask: SzMask = SzMask()
    masked_data: dict = sz_mask.mask_data(exp_data)
    masked_text: str = json.dumps(masked_data)
    obs_data: dict = json.loads(sz_mask.unmask_text(masked_text))

    assert sorted(exp_data.items()) == sorted(obs_data.items())


if __name__ == "__main__":
    test_mask(debug = True)
