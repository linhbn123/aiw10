from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.shell.tool import ShellTool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from app.utils import constants, commonutils
from app.tools import gittools


def beautify(repo_path, pr_number, source_branch):
    # List of tools to use
    tools = [
        ShellTool(ask_human_input=False),
        gittools.clone_repo,
        gittools.switch_to_local_repo_path,
        gittools.checkout_source_branch,
        gittools.get_files_from_pull_request,
        gittools.run_autopep8,
        gittools.has_changes,
        gittools.commit_and_push
    ]

    # Configure the language model
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Set up the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a Python expert. 
                You always write code following code convention and best practices in PEP8. 
                Your audience are experienced engineers and managers.
                """,
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
    Clone the repository {repo_path} to local directory {local_repo_path}.
    Then in that local directory, 
    checkout the source branch {source_branch} of pull request number {pr_number},
    beautify all the code in the .py source code files 
    changed by the pull request as per pep8 standards, 
    commit the change and push to the remote repository.
    Make sure to not touch the non-python source code files.
    """
    list(agent_executor.stream({"input": user_prompt}))
