#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example using `sz_semantics` to mask PII values in Senzing JSON.

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import json
import pathlib
import sys
import typing

from sz_semantics import SzMask


if __name__ == "__main__":
    sz_mask: SzMask = SzMask()

    ## load a JSON file to use as input, from the CLI argument
    data_path: str = sys.argv[1]

    data: typing.Any = json.load(
        open(
            pathlib.Path(data_path),
            "r",
            encoding = "utf-8",
        ),
    )

    ## mask the PII values in the data
    masked_data: typing.Any = sz_mask.mask_data(
        data,
        debug = False, # True
    )

    masked_text: str = json.dumps(
        masked_data,
        indent = 2,
    )

    print("   ###  MASKED PII:")
    print(masked_text)

    ## unmask a text representation of the same data
    print("\n\n")
    print("   ###  UNMASKED PII:")
    print(sz_mask.unmask_text(masked_text))
