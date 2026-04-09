from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers.auth_router import router
import os
from routers.today_router import router as today_router
from routers.stt_router import router as stt_router
from routers.hint_router import router as hint_router

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "https://lexiome.solmi.wiki"
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# routers
app.include_router(router)
app.include_router(today_router)
app.include_router(stt_router)
app.include_router(hint_router)

# static
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")