from fastapi import APIRouter
from pydantic import BaseModel
import os
import structlog
from google import genai
from ..core.database import reset_database

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/config", tags=["Configuration"])

class ConfigPayload(BaseModel):
    repoUrl: str
    githubToken: str
    useSandbox: bool
    geminiKey: str
    geminiModel: str = "gemini-1.5-pro"
    slackWebhook: str = ""
    jiraToken: str = ""
    awsAccessKey: str = ""

@router.post("/")
async def set_configuration(payload: ConfigPayload):
    """Store environment variables dynamically from onboarding."""
    os.environ["TARGET_REPO_URL"] = payload.repoUrl
    if payload.githubToken:
        os.environ["GITHUB_TOKEN"] = payload.githubToken
    if payload.geminiKey:
        os.environ["GEMINI_API_KEY"] = payload.geminiKey
        os.environ["GEMINI_MODEL"] = payload.geminiModel
    
    if payload.slackWebhook:
        os.environ["SLACK_WEBHOOK"] = payload.slackWebhook
    if payload.jiraToken:
        os.environ["JIRA_TOKEN"] = payload.jiraToken
    if payload.awsAccessKey:
        os.environ["AWS_ACCESS_KEY"] = payload.awsAccessKey
        
    os.environ["USE_REAL_SANDBOX"] = "true" if payload.useSandbox else "false"
    
    # Purge old DB and seed new repo node
    await reset_database(payload.repoUrl)
    
    logger.info("configuration_updated", repo=payload.repoUrl, sandbox=payload.useSandbox)
    return {"status": "success", "message": "Configuration applied"}

class ModelsRequest(BaseModel):
    apiKey: str

@router.post("/models")
async def get_gemini_models(req: ModelsRequest):
    """Fetch available Gemini models using the provided API key."""
    try:
        client = genai.Client(api_key=req.apiKey)
        # Fetch models from Gemini API
        models_iterator = client.models.list()
        
        # Filter for models that support generateContent (text generation) and contain 'gemini'
        available_models = []
        for model in models_iterator:
            if "gemini" in model.name.lower() and "generateContent" in model.supported_actions:
                available_models.append({
                    "name": model.name,
                    "displayName": model.display_name or model.name,
                    "description": model.description
                })
                
        # Sort so the newest models are at the top (e.g. 1.5 pro)
        available_models.sort(key=lambda x: x["name"], reverse=True)
        return {"status": "success", "models": available_models}
    except Exception as e:
        logger.error("failed_to_fetch_models", error=str(e))
        return {"status": "error", "message": str(e)}

