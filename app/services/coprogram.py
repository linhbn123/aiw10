from github import Github
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools.shell.tool import ShellTool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from app.utils import constants, commonutils, promptutils, githubutils
from app.tools import gittools, filetools
from app.api import env


def address_review_comments(repo_path, pr_number, source_branch, comments):
    pr = githubutils.get_pr(repo_path, pr_number)

    # Get the diffs of the pull request
    diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        } 
        for file in pr.get_files()
    ]
    
    # List of tools to use
    tools = [
        ShellTool(ask_human_input=True),
        gittools.clone_repo,
        gittools.switch_to_local_repo_path,
        gittools.checkout_source_branch,
        gittools.commit_and_push,
        filetools.create_directory,
        filetools.find_file,
        filetools.create_file,
        filetools.update_file
    ]

    # Configure the language model
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # Set up the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a senior python developer. You excel at communicating with other developers and writing clean, optimized code.
                If you're asked for opinions, you give detailed and specific actionable feedback.
                You aren't rude, but you don't worry about being polite either.
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

    # Format data for OpenAI prompt
    user_prompt = promptutils.construct_coprogram_prompt(repo_path, local_repo_path, pr_number, source_branch, diffs, comments)
    list(agent_executor.stream({"input": user_prompt}))
