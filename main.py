from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from auth_router import router
import os

app = FastAPI()
app.include_router(router)

# 프론트 cors 허용
origins = [
  "http://localhost:5173",
  "https://vagant.solmi.wiki"
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# api
@app.get("/api/hello")
def hello():
  return {"message": "hello"}

# static
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")