from fastapi import FastAPI
from routers import auth
from routers import evidence
from routers import agents
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # The Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(evidence.router)
app.include_router(agents.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

