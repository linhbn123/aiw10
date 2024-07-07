import functools

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool
from langgraph.graph import StateGraph, END

from app.utils import constants, commonutils
from app.utils.agentutils import AgentState, create_agent, agent_node
from app.tools.gittools import clone_repo, switch_to_local_repo_path, checkout_source_branch, generate_branch_name, create_branch_and_push, create_pull_request, link_issue_to_pull_request
from app.tools.filetools import create_directory, find_file, create_file, update_file


def implement_task(repo_path: str, issue_number: int, issue_title: str, issue_body: str):
    tavily_tool = TavilySearchResults(max_results=5)

    # This tool executes code locally, which can be unsafe. Use with caution.
    python_repl_tool = PythonREPLTool()

    members = ["Researcher", "Coder", "Reviewer", "QATester", "FileWriter", "CheckoutAgent", "PrAgent"]
    system_prompt = (
        f"You are a supervisor tasked with managing a conversation between the"
        f" following workers:  {members}. Given the following user request,"
        f" respond with the worker to act next. Each worker will perform a"
        f" task and respond with their results and status. When finished,"
        f" respond with FINISH."
    )

    options = members + ["FINISH"]

    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                }
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                f"system",
                f"Given the conversation above, who should act next?"
                f" Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    llm = ChatOpenAI(model="gpt-4o")

    supervisor_chain = (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )

    research_agent = create_agent(llm, [tavily_tool], "You are a web researcher.")
    research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")

    review_agent = create_agent(llm, [tavily_tool],
                                """You are a senior developer. You excel at code reviews.
                                You give detailed and specific actionable feedback.
                                You aren't rude, but you don't worry about being polite either.
                                Instead you just communicate directly about technical matters.
                                """)
    review_node = functools.partial(agent_node, agent=review_agent, name="Reviewer")

    test_agent = create_agent(
        llm,
        [python_repl_tool],  # DANGER DANGER runs arbitrary Python code
        "You may generate safe python code to test functions and classes using unittest or pytest.",
    )
    test_node = functools.partial(agent_node, agent=test_agent, name="QATester")

    code_agent = create_agent(
        llm,
        [python_repl_tool],  # ALSO DANGER DANGER
        "You may generate safe python code to analyze data with pandas and generate charts using matplotlib.",
    )
    code_node = functools.partial(agent_node, agent=code_agent, name="Coder")

    write_agent = create_agent(
        llm,
        [create_directory, create_file, find_file, update_file],
        "Write the generated code to files.",
    )
    write_node = functools.partial(agent_node, agent=write_agent, name="FileWriter")

    local_repo_path = constants.ROOT_DIR + '/' + commonutils.get_repo_identifier(repo_path) + '-' + commonutils.get_formatted_current_timestamp()

    checkout_agent = create_agent(
        llm,
        [clone_repo, switch_to_local_repo_path, checkout_source_branch],
        (
            "You're tasked with preparing the local git repository for other agents to work on it. ",
            f"The repository path is {repo_path}, the local repository path is {local_repo_path} "
            "and the source branch is main."
            ),
    )
    checkout_node = functools.partial(agent_node, agent=checkout_agent, name="CheckoutAgent")

    pr_agent = create_agent(
        llm,
        [generate_branch_name, create_branch_and_push, create_pull_request, link_issue_to_pull_request],
        (
            "You're tasked with checking if there are local changes, and if yes, "
            "prepare a pull request targetting main and then link that pull request "
            f"with the issue number {issue_number}. The repository path is {repo_path}, "
            f"the local repository path is {local_repo_path} and the source branch "
            "is auto-generated"),
    )
    pr_node = functools.partial(agent_node, agent=pr_agent, name="PrAgent")

    workflow = StateGraph(AgentState)
    workflow.add_node("Reviewer", review_node)
    workflow.add_node("Researcher", research_node)
    workflow.add_node("Coder", code_node)
    workflow.add_node("QATester", test_node)
    workflow.add_node("FileWriter", write_node)
    workflow.add_node("CheckoutAgent", checkout_node)
    workflow.add_node("PrAgent", pr_node)
    workflow.add_node("supervisor", supervisor_chain)

    for member in members:
        workflow.add_edge(member, "supervisor")

    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)

    workflow.set_entry_point("CheckoutAgent")

    graph = workflow.compile()

    initial_state = AgentState(
        messages=[HumanMessage(content=f"""
                            Raise a pull request to implement the following task:
                            Github Issue Number: {issue_number}
                            Github Issue Title: {issue_title}
                            Github Issue Content: {issue_body}
                            """)],
        next="CheckoutAgent"
    )

    print(graph.invoke(initial_state))
