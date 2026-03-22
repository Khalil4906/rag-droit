from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import (
    AgentExecutor,  
    create_tool_calling_agent,  
)
from langchain_core.prompts import (
    ChatPromptTemplate,  
    MessagesPlaceholder,  
)
from langchain_core.messages import (
    BaseMessage,   
    HumanMessage,  
)

from app.core.config import get_settings  
from app.agents.prompt_store import prompt_store  
from app.tools.search_documents import search_documents  


def _build_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0,
        max_output_tokens=2048,
    )


def _build_rag_agent(
    system_prompt: str,
) -> AgentExecutor:
    llm = _build_llm()  

    tools = [search_documents]  

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            system_prompt,  
        ),
        MessagesPlaceholder("chat_history"),  
        ("human", "{input}"),                 
        MessagesPlaceholder("agent_scratchpad"),  
    ])

    agent = create_tool_calling_agent(
        llm,    
        tools,  
        prompt, 
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=3,       
        handle_parsing_errors=True,  
        verbose=False,          
    )


async def _run_chat(
    message: str,
    history: list[BaseMessage],
    system_prompt: str,
) -> str:
    llm = _build_llm()  

    messages = (
        [("system", system_prompt)]
        + [(
            "human" if isinstance(m, HumanMessage) else "assistant",
            m.content,
        ) for m in history]
        + [("human", message)]
    )

    response = await llm.ainvoke(messages)

    return response.content  


async def _run_rag(
    message: str,
    history: list[BaseMessage],
    system_prompt: str,
) -> str:
    agent_executor = _build_rag_agent(system_prompt)

    result = await agent_executor.ainvoke({
        "input": message,           
        "chat_history": history,    
    })

    return result["output"]


async def run_agent(
    message: str,
    intent: str,
    history: list[BaseMessage],
    session_id: str,
) -> dict:

    from app.db.conversations import save_message

    prompts = prompt_store.load()

    await save_message(
        session_id=session_id,  
        role="human",           
        content=message,        
        intent=intent,          
    )

    try:
        if intent == "chat":
            answer = await _run_chat(
                message=message,
                history=history,
                system_prompt=prompts.system_prompt,
            )
            sources_used = False  

        elif intent == "rag":
            answer = await _run_rag(
                message=message,
                history=history,
                system_prompt=prompts.system_prompt,
            )
            sources_used = True  #

        elif intent == "summarize":
            answer = (
                "La fonctionnalité de résumé sera disponible "
                "prochainement."
            )
            sources_used = False

        else:
            answer = (
                "La fonctionnalité de fiche de révision sera "
                "disponible prochainement."
            )
            sources_used = False

    except Exception as e:
        answer = (
            "Une erreur est survenue lors du traitement "
            f"de ta question : {str(e)}. "
            "Réessaie dans quelques instants."
        )
        sources_used = False

    await save_message(
        session_id=session_id,  
        role="assistant",       
        content=answer,         
        intent=None,            
    )

    return {
        "answer": answer,            
        "intent": intent,            
        "sources_used": sources_used,  
    }