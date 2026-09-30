import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run("speech.app:app", host=os.environ.get("SPEECH_BIND_HOST", "127.0.0.1"),
                port=8010, workers=1, limit_concurrency=8, timeout_keep_alive=5)
