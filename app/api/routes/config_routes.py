from fastapi import APIRouter, HTTPException  

from app.schemas.chat import PromptConfig  
from app.agents.prompt_store import prompt_store  


router = APIRouter()  


@router.get("/config", response_model=PromptConfig)
async def get_config() -> PromptConfig:
    try:
        prompts = prompt_store.load()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du chargement des prompts : {str(e)}",
        )

    return PromptConfig(
        system_prompt=prompts.system_prompt,  
        rag_prompt=prompts.rag_prompt,        
    )


@router.put("/config", response_model=PromptConfig)
async def update_config(body: PromptConfig) -> PromptConfig:
    if "{context}" not in body.rag_prompt:
        raise HTTPException(
            status_code=422,  
            detail=(
                "Le rag_prompt doit contenir {context} — "
                "placeholder pour les passages trouvés par la recherche."
            ),
        )

    if "{question}" not in body.rag_prompt:
        raise HTTPException(
            status_code=422,
            detail=(
                "Le rag_prompt doit contenir {question} — "
                "placeholder pour la question de l'étudiant."
            ),
        )

    try:
        prompt_store.save(
            system_prompt=body.system_prompt,  
            rag_prompt=body.rag_prompt,        
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la sauvegarde : {str(e)}",
        )

    return PromptConfig(
        system_prompt=body.system_prompt,
        rag_prompt=body.rag_prompt,
    )


@router.post("/config/reset", response_model=PromptConfig)
async def reset_config() -> PromptConfig:
    try:
        prompts = prompt_store.reset()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la réinitialisation : {str(e)}",
        )

    return PromptConfig(
        system_prompt=prompts.system_prompt,  
        rag_prompt=prompts.rag_prompt,        
    )