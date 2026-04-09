from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
from vosk import Model, KaldiRecognizer

router = APIRouter()

MODEL_PATH = "./models/vosk-model-small-ru-0.22"
model = Model(MODEL_PATH)

@router.websocket("/ws/stt")
async def stt_ws(websocket: WebSocket):
    await websocket.accept()

    rec = KaldiRecognizer(model, 16000)

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data["type"] == "audio":
                audio_bytes = base64.b64decode(data["data"])

                if rec.AcceptWaveform(audio_bytes):
                    result = json.loads(rec.Result())
                    await websocket.send_json({
                        "type": "final",
                        "text": result.get("text", "")
                    })
                else:
                    partial = json.loads(rec.PartialResult())
                    await websocket.send_json({
                        "type": "partial",
                        "text": partial.get("partial", "")
                    })

    except WebSocketDisconnect:
        # 정상 종료
        pass