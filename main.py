from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 개발서버 cors 허용
origins = [
  "http://localhost:5173"
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
app.mount("/", StaticFiles(directory="dist", html=True), name="static")