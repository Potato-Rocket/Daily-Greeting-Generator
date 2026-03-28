# Plan

## Config reorganization

1. ~~Move ollama url to regular config - yaml and .env are kind of equally secure and it's easier to parse~~
2. ~~Change config to YAML, update example~~
3. ~~Store variables in config class intstead of in each file, so defaults are in one place~~
4. ~~Have modules call on the config class rather than overwriting constants, cleaner~~

## LLM improvements

1. ~~Figure out how to combine the two functions since they're redundant aside from the variable they use~~
2. ~~Add optional parameters for temperature, whether or not to use thinking~~
3. ~~Implements specification and verification of json format~~ — decided against; current VERDICT pattern matching is simple and sufficient
4. ~~Consider where to use thinking and where to use structured reasoning~~ — prompt structure already handles this; cutting thinking gave 5x speedup
5a. ~~Use Jinja templates for prompts — separate prompt content from pipeline logic~~
5. ~~Can we specify the desired response length? Then we could bring back the random lognormal length determination~~
6. Switch from Ollama to a llama.cpp server with OpenAI API for speed improvements
7. Consider whether to remove certain seldom-changed config options, such as for excerpts
8. What llm options should be configurable?

## Data source improvements

1. Use python lib for NOAA
2. Use httpx to make multiple project gutenberg requests synchronously, queue them as they come in, longer timeout, etc... OR selfhost a gutendex instance!
3. Figure out why the navidrome API isn't using my laptop's ssl certs
4. Consider other data sources to add it - qwen is more capable
