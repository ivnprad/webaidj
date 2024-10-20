from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

origins = [
    "http://localhost:3000", # vue3 app
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

class Command(BaseModel):
    ip_address: str
    component: str
    command: str
    data_type: str
    payload: int = None

@app.post("/api/toggle-shuffle")
def toggle_shuffle(command: Command):
    try:
        if command.payload == None:
            raise HTTPException(status_code=400, detail="Payload is required")
        response = {
            "message": "we got you"
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

