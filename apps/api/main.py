from fastapi import FastAPI
from routers import auth
from routers import evidence
from routers import agents

app = FastAPI()
app.include_router(auth.router)
app.include_router(evidence.router)
app.include_router(agents.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

