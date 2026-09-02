import os
import json
import datetime
from fastapi import FastAPI, Body, Header, HTTPException, Cookie, Response, Depends, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from jinja2 import Template
from fastapi.responses import StreamingResponse
import asyncio
import uvicorn
from lib.signal_manager import SignalManager
from lib.load_static import TemplateMap
from websockets.exceptions import ConnectionClosed


app = FastAPI()


GOOGLE_CLIENT_ID = "223025000144-h24fpvolha8m78bl0askl3sal4agvbt2.apps.googleusercontent.com"
SECRET_KEY = "oh-lord-in-heave-983409-pullu-pullu"  # Change in production
ALGORITHM = "HS256"

signal_manager = SignalManager()
static_loader = TemplateMap.get_instance()


class GoogleAuthPayload(BaseModel):
    token: str
    
# --- 2. AUTH DEPENDENCY (PROTECTS ROUTES) ---
def get_current_user(session_token: str | None = Cookie(default=None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Verify custom app JWT from cookie
        payload = jwt.decode(session_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

async def my_generator():
    while True:
    # Crucial: Data must still be manually formatted in the SSE syntax
        yield "data: Hello from the server!\n\n"
        await asyncio.sleep(1)


@app.get("/stream")
async def stream_endpoint():
    # You MUST explicitly declare the media_type here
    return StreamingResponse(my_generator(), media_type="text/event-stream")

# --- page ---
@app.get("/")
def rool_path():
    with open(os.path.join("ui", "main.template"), "r") as f:
        initial_ui = f.read()
    response = Response(content=initial_ui, status_code=200)
    response.headers["content-type"] = "text/html"
    return response
    
@app.get("/page/login")
def page_login():
    with open(os.path.join("ui", "login.template"), "r") as f:
        initial_ui = f.read()
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response

# --- 1. LOGIN ROUTE ---
@app.post("/api/auth/google")
def google_auth(payload: GoogleAuthPayload, response: Response):
    try:
        # Verify Google Token
        id_info = id_token.verify_oauth2_token(
            payload.token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # Build app session payload
        session_data = {
            "sub": id_info["sub"],
            "email": id_info["email"],
            "name": id_info.get("name"),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        }

        # Sign custom app session JWT
        session_token = jwt.encode(session_data, SECRET_KEY, algorithm=ALGORITHM)

        # Set HttpOnly Cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,     # Prevents JavaScript XSS access
            secure=True,       # HTTPS only (set False for local HTTP testing)
            samesite="lax",    # Protection against CSRF
            max_age=604800     # 7 days in seconds
        )

        return {"message": "Login successful", "email": id_info["email"]}

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

# --- 3. PROTECTED ROUTE EXAMPLE ---
@app.get("/api/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome back, {user['name'] if user.get('name') else user['email']}!",
        "user_id": user["sub"]
    }

# --- 4. LOGOUT ROUTE ---
@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

@app.get("/page/main")
def main_page():
    with open(os.path.join("ui", "main.template"), "r") as f:
        initial_ui = f.read()
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response
    
# ============== Signal websocket===
@app.websocket("/ws/signal")
async def websocket_signal(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                data = await websocket.receive_text()
                data_json = json.loads(data)
                print(data_json)
                result = signal_manager.signal_directive_switch(websocket, data_json)
                await websocket.send_json(result)
            except Exception as e:
                await websocket.send_json({"Server error": "{}".format(str(e))})
    except (WebSocketDisconnect, ConnectionClosed) as rrr:
        print("Exception capture on websocket connection", rrr)
        del signal_manager.socket_altname[websocket]
        

# --- static file ---
@app.get("/static")
@app.get("/static/{tpath:path}")
def static_files(tpath=None):
    if tpath:
        typ = tpath.split(os.sep)
        print("==> ", typ)
        content = static_loader.get_template(typ[0], typ[1])
    else:
        content = static_loader.list_dir()
    response = Response(content=content, status_code=200)
    return response


# ============== Start the server
if os.environ.get("SSL") == "true":
    # import ssl
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain(, keyfile=)
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile=os.path.join("cer", "main.cer"), ssl_keyfile=os.path.join(
        "cer", "main.key"), reload=False)
else:
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
