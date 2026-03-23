from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from auth_router import router
import os

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "https://vagant.solmi.wiki"
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(router)

# api
@app.get("/api/hello")
def hello():
  return {"message": "hello"}

# static
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")