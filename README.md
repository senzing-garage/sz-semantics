# sz_semantics

Transform JSON output from the [Senzing SDK](https://senzing.com/docs/python/)
for use with graph technologies, semantics, and downstream LLM integration.

## Usage: Masking PII

Mask the PII values within Senzing JSON output with tokens which can
be substituted back later. For example, _mask_ PII values before
calling a remote service (such as an LLM-based chat) then _unmask_
returned text after the roundtrip, to maintain _data privacy_.

```python
import json
from sz_semantics import Mask

data: dict = { "ENTITY_NAME": "Robert Smith" }

sz_mask: Mask = Mask()
masked_data: dict = sz_mask.mask_data(data)

masked_text: str = json.dumps(masked_data)
print(masked_text)

unmasked: str = sz_mask.unmask_text(masked_text)
print(unmasked)
```


## Install

```bash
pip install sz_sematics
```


## Demo

Run the `demo.py` script with an example JSON data file:

```bash
python3 demo.py data/get.json
```


<details>
  <summary>License and Copyright</summary>

Source code for `sz_semantics` plus any logo, documentation, and
examples have an [MIT license](https://spdx.org/licenses/MIT.html)
which is succinct and simplifies use in commercial applications.

All materials herein are Copyright © 2025 Senzing, Inc.
</details>
