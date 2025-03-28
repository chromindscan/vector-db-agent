# Vector DB Extension

## Setup

### Register extension in directory-chain

The nodes in the network must add the extension to make it available for containers to use. This is already done on official networks, but in case you run your own node(s) you will need to run this command:

```shell
pmc subnode-image add --name vector_db_extension \
  --url registry.gitlab.com/chromaway/core/vector-db-extension/chromaway/vector-db-extension-chromia-subnode \
  --digest latest \
  --image-description "Extension to Postchain for Postgres Vector DB support" \
  -gtx net.postchain.gtx.extensions.vectordb.VectorDbGTXModule
```

Replace the `<digest>` with the latest image version found [here](https://gitlab.com/chromaway/core/vector-db-extension/container_registry/8296249).

### Blockchain configuration

Update your blockchain config to include the following:

```yaml
blockchains:
  my_chain:
    module: my_chain_module
    config:
      gtx:
        modules:
          - "net.postchain.gtx.extensions.vectordb.VectorDbGTXModule"
      vector_db_extension:
        dimensions: 300 # Set number of dimensions to use
```

And make sure you deploy your chain to a container with the extension supported.

## How to use in the dApp

### Rell library

There is a optional but recommended library available to store vectors:

```yaml
  vector_db:
    registry: https://gitlab.com/chromaway/core/vector-db-extension.git
    path: rell/src/lib/
    tagOrBranch: <version>
    rid: x"<rid>" # Update to match version
    insecure: false
```

Set `<version>` with [latest version](https://gitlab.com/chromaway/core/vector-db-extension/-/tags), run `chr install` and then update the `rid` to what they output says it is (`Was: ...`).

Once installed you can add and remove vectors by calling the `store_vector` or `delete_vector` functions.

### Insert vectors

Simple dapp to store and remove vectors:

```
import lib.vector_db.*;

operation add_vector(context: integer, vector: text, id: integer) {
    store_vector(context, vector, id);
}

operation delete_vector(context: integer, id: integer) {
    delete_vector(context, id);
}
```

### Querying vectors

The extension will add a query function named `query_closest_objects` which can be called to search vectors.

It supports the following parameters:


| Name             | Type             | Required | Default | Description                                                                                       |
|------------------|------------------|----------|---------|---------------------------------------------------------------------------------------------------|
| `context`        | `integer`        | true     |         | Context used by dApp. Can be any number and a dApp can use multiple contexts to separate vectors. |
| `q_vector`       | vector as `text` | true     |         | The vector to search for as `text` on format `[1,2,3]`.                                           |
| `max_distance`   | `decimal`        | true     |         | The max distance from `q_vector` to stored vectors                                                |
| `max_vectors`    | `integer`        | false    | 10      | The max number of vectors to return.                                                              |
| `query_template` | `text`           | false    | Not set | Provide a Rell query function to transform the results (see below).                               |

### Query template

When no `query_template` is provided to `query_closest_objects` the result returned is a list of vector ids and their distance. This can however be transformed by providing a Rell query function:

```
query get_messages(closest_results: list<object_distance>): list<text> {
    val closest_result_ids = closest_results @ {} ( @set(rowid(.id)) );
    return message @ { .rowid in closest_result_ids } ( .text );
}
```

This function will transform the vector search result `closest_results: list<object_distance>` into a list of text. When `query_template=get_messages` is provided to `query_closest_objects` the result will be a list of text. 

## Local run and example

This requires:
 - Docker
 - `chr`
 - `pmc`

Setup a node locally by using the [directory1-example image](https://gitlab.com/chromaway/example-projects/directory1-example/-/blob/dev/docs/images.md?ref_type=heads).

```bash
docker run --rm -it -p 7740:7740 registry.gitlab.com/chromaway/example-projects/directory1-example/managed-single:latest
```

In a separate terminal with `pmc` setup:

```bash
# Build the demo dapp
cd vector-db-extension/rell
chr build

# Add the demo dapp
pmc blockchain add -bc vector-db-extension/rell/build/vector_example.xml -c dapp -n vector_blockchain

# Get the blockchain rid - can be found manually from "pmc blockchains"
vector_brid=$(pmc blockchains | jq -r '.[] | select(.Name == "vector_blockchain") | .Rid')

```

Add some messages:

```bash
chr tx -brid $vector_brid add_message hej "[1.0, 2.0, 3.0]"
chr tx -brid $vector_brid add_message hello "[1.0, 2.5, 3.0]"
chr tx -brid $vector_brid add_message hei "[1.0, 2.0, 3.1]"
chr tx -brid $vector_brid add_message "guten tag" "[1.0, 1.5, 3.5]"
```

A few example queries:

```bash
# Plain query with no query_template:
chr query -brid $vector_brid query_closest_objects context=0 q_vector="[1.0, 2.0, 3.0]" max_distance=1.0 max_vectors=2
[
  [
    "distance": "0",
    "id": 1
  ],
  [
    "distance": "0.0001212999220387978",
    "id": 3
  ]
]

# Basic query_template provided to return the text messages:
chr query -brid $vector_brid query_closest_objects context=0 q_vector="[1.0, 2.5, 3.0]" max_distance=1.0 max_vectors=2 'query_template=["type":"get_messages"]'
[
  "hello",
  "hej"
]

# Another query_template which returns text and distance:
chr query -brid $vector_brid query_closest_objects context=0 q_vector="[1.0, 2.5, 3.0]" max_distance=1.0 max_vectors=2 'query_template=["type":"get_messages_with_distance"]'
[
  [
    "distance": "0",
    "text": "hello"
  ],
  [
    "distance": "0.005509683802306209",
    "text": "hej"
  ]
]

# Additional arguments passed to the query_template function
chr query -brid $vector_brid query_closest_objects context=0 q_vector="[1.0, 2.5, 3.0]" max_distance=1.0 max_vectors=2 'query_template=["type":"get_messages_with_filter", "args":["text_filter": "j"]]'
[
  "hej",
]
```