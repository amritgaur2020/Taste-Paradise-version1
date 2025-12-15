from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    intent: str

@app.post("/api/chatbot/message")
async def test_chatbot(chat: ChatMessage):
    return ChatResponse(
        response=f"Got: {chat.message}",
        intent="test"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
