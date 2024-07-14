from langchain_community.tools.shell.tool import ShellTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from app.utils import constants, commonutils
from app.tools import gittools, pineconetools


def upload(repo_path):
    # List of tools to use
    tools = [
        ShellTool(ask_human_input=False),
        gittools.clone_repo,
        gittools.switch_to_local_repo_path,
        pineconetools.upload_python_source_code_to_pinecone
    ]

    # Configure the language model
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Set up the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a langchain and pinecone expert.",
            ),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    local_repo_path = constants.ROOT_DIR + '/' + commonutils.get_repo_identifier(repo_path) + '-' + commonutils.get_formatted_current_timestamp()

    # Bind the tools to the language model
    llm_with_tools = llm.bind_tools(tools)

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    user_prompt = f"""
    Clone the repository to the local directory.
    Then upload all python source code to pinecone.
    The repository path is {repo_path} and the local repository path is {local_repo_path}.
    """
    list(agent_executor.stream({"input": user_prompt}))
