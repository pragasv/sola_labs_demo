from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from Agent_request_call import agent_request_process, creative_reaction_request_process

app = FastAPI(title="Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentResponse(BaseModel):
    answer: str


@app.post("/agent/process", response_model=AgentResponse)
async def process_agent_request(
    prompt_text: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    file_content = None
    if file is not None:
        file_content = await file.read()

    answer = agent_request_process(
        prompt_text=prompt_text,
        file_content=file_content
    )
    return AgentResponse(answer=answer)


# NEW: Creative reaction endpoint (image + headline + personas)
@app.post("/creative/react", response_model=AgentResponse)
async def creative_react(
    headline: str = Form(...),
    personas_json: str = Form(...),
    image: UploadFile = File(...),
):
    """
    personas_json example:
    {
      "hcp_early": "Dermatologist, 8 years, early adopter...",
      "hcp_conservative": "Dermatologist, 15 years, conservative...",
      "patient_new": "Newly diagnosed patient...",
      "patient_long": "Long-term patient..."
    }
    """
    image_bytes = await image.read()
    answer = creative_reaction_request_process(
        headline=headline,
        personas_json=personas_json,
        image_bytes=image_bytes,
        image_mime=image.content_type or "image/png"
    )
    return AgentResponse(answer=answer)