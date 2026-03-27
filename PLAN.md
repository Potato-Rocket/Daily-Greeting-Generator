# Plan

## Config reorganization

1. ~~Move ollama url to regular config - yaml and .env are kind of equally secure and it's easier to parse~~
2. ~~Change config to YAML, update example~~
3. ~~Store variables in config class intstead of in each file, so defaults are in one place~~
4. ~~Have modules call on the config class rather than overwriting constants, cleaner~~

## LLM improvements

1. Figure out how to combine the two functions since they're redundant aside from the variable they use
2. ~~Add optional parameters for temperature, whether or not to use thinking~~
3. Implements specification and verification of json format, particularly for the strict or multi-part responses, use raw to avoid weird default templates
4. Consider where to use thinking and where to use structured reasoning
5. ~~Can we specify the desired response length? Then we could bring back the random lognormal length determination~~
