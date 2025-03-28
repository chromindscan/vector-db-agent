# Chromia Vector DB Extension

### Local Development

1. **Start a local Chromia node using Docker**:
   ```bash
   docker run --rm -it -p 7740:7740 registry.gitlab.com/chromaway/example-projects/directory1-example/managed-single:latest
   ```
   Take note of the following from the logs:
   - Directory chain BRID
   - Provider private/public keys
   - Container name ("dapp")

2. **Update your blockchain configuration** in `rell/chromia.yml`:
   ```yaml
   blockchains:
     vector_example:
       module: vector_example
       config:
         gtx:
           modules:
             - "net.postchain.gtx.extensions.vectordb.VectorDbGTXModule"
         vector_db_extension:
           dimensions: 1538 # Adjust based on your vector model. Use 1536 for OpenAI text-small
   deployments:
     local:
       brid: x"97E2F94CBB353CB62CB3E49C190F97C8A7B1A77418FD1262E7B16DB22179C530"
       url: http://localhost:7740
       container: dapp
   ```

4. **Build your Rell application in the same directory as vector_example.XML file**:
   ```bash
   cd rell
   chr build
   ```

5. **Deploy to your local node**:
   ```bash
   pmc blockchain add -bc build/vector_example.xml -c dapp -n vector_blockchain
   ```

6. **Get your blockchain RID**:
   ```bash
   vector_brid=$(pmc blockchains | jq -r '.[] | select(.Name == "vector_blockchain") | .Rid')
   echo $vector_brid
   ```


### Basic Operations

**Store a vector with text**:
```bash
chr tx -brid $vector_brid add_message "Your text here" "[1.0, 2.0, 3.0]"
```

**Query for similar vectors**:
```bash
chr query -brid $vector_brid query_closest_objects context=0 q_vector="[1.0, 2.5, 3.0]" max_distance=1.0 max_vectors=2 'query_template=["type":"get_messages_with_distance"]'
```