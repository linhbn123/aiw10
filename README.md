# aiw10

Update `bootstrap.sh` environment variables, then build a docker image:
```shell
docker build -t aiw10 .
```

Start a docker container locally:
```shell
docker rm aiw10
docker run --name aiw10 -it -p 5000:5000 -v /path/to/a/local/dir:/data -e BOOT_USERNAME='BOOT_USERNAME' -e PINECONE_API_KEY='PINECONE_API_KEY' -e GITHUB_TOKEN='GITHUB_TOKEN' -e OPENAI_API_KEY='OPENAI_API_KEY' -e TAVILY_API_KEY='TAVILY_API_KEY' -e LANGCHAIN_ENDPOINT='https://api.smith.langchain.com' -e LANGCHAIN_PROJECT='default' -e LANGCHAIN_TRACING_V2=true -e LANGCHAIN_API_KEY='LANGCHAIN_API_KEY' aiw10
```

E.g.
```shell
docker build -t aiw10 . && (docker rm aiw10 || true) && mkdir -p /tmp/aiw10 && docker run --name aiw10 -it -p 5000:5000 -v /tmp/aiw10:/data -e BOOT_USERNAME='BOOT_USERNAME' -e PINECONE_API_KEY='PINECONE_API_KEY' -e GITHUB_TOKEN='GITHUB_TOKEN' -e OPENAI_API_KEY='OPENAI_API_KEY' -e TAVILY_API_KEY='TAVILY_API_KEY' -e LANGCHAIN_ENDPOINT='https://api.smith.langchain.com' -e LANGCHAIN_PROJECT='default' -e LANGCHAIN_TRACING_V2=true -e LANGCHAIN_API_KEY='LANGCHAIN_API_KEY' aiw10
```
