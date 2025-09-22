# sz_semantics

Transform JSON output from the [Senzing SDK](https://senzing.com/docs/python/)
for use with graph technologies, semantics, and downstream LLM integration.


## Install

```bash
pip install sz_sematics
```


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

For an example, run the `demo1.py` script with a data file which
captures Senzing JSON output:

```bash
python3 demo1.py data/get.json
```


## Usage: Semantic Represenation

Starting with a small [SKOS-based taxonomy](https://www.w3.org/2004/02/skos/),
parse the Senzing [_entity resolution_](https://senzing.com/what-is-entity-resolution/)
(ER) results to generate an 
[`RDFlib`](https://rdflib.readthedocs.io/) _semantic graph_
then transform this into a 
[`NetworkX`](https://networkx.org/) _property graph_, which represents a 
[_semantic layer_](https://enterprise-knowledge.com/what-is-a-semantic-layer-components-and-enterprise-applications/).
In other words, generate the "backbone" for constructing an
[_Entity Resolved Knowledge Graph_](https://senzing.com/entity-resolved-knowledge-graphs/).

```python
import pathlib
from sz_semantics import Thesaurus

thes: Thesaurus = Thesaurus()

thes.parse_er_export(
    [
        "data/truth/customers.json",
        "data/truth/reference.json",
        "data/truth/watchlist.json",
    ],
    export_path = pathlib.Path("data/truth/export.json"),
    er_path = pathlib.Path("thesaurus.ttl"),
)

thes.load_er_thesaurus(
    er_path = pathlib.Path("thesaurus.ttl"),
)

thes.save_sem_layer(pathlib.Path("sem.json"))
```

For an example, run the `demo2.py` script to process the JSON file
`data/export.json` which captures Senzing ER exported results:

```bash
python3 demo2.py
```

Check the generated RDF in `thesaurus.ttl` and the resulting property
graph in the `sem.json` node-link format file.


---

<details>
  <summary>License and Copyright</summary>

Source code for `sz_semantics` plus any logo, documentation, and
examples have an [MIT license](https://spdx.org/licenses/MIT.html)
which is succinct and simplifies use in commercial applications.

All materials herein are Copyright © 2025 Senzing, Inc.
</details>

Kudos to 
[@brianmacy](https://github.com/brianmacy),
[@jbutcher21](https://github.com/jbutcher21),
[@cj2001](https://github.com/cj2001),
[@docktermj](https://github.com/docktermj),
and the kind folks at [GraphGeeks](https://graphgeeks.org/) for their support.
</details>


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=senzing-garage/sz-semantics&type=Date)](https://star-history.com/#senzing-garage/sz-semantics&Date)
