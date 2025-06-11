#!/usr/bin/env python3
"""
Test simple FastAPI app
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World", "status": "working"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting test app on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 