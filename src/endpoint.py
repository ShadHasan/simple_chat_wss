import os
import uuid
import time
import asyncio
import datetime
import json
import uvicorn
import threading
from fastapi import FastAPI, Body, Header, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from websockets.exceptions import ConnectionClosed
from jinja2 import Template
from starlette.concurrency import run_in_threadpool
import imageio.v3 as iio

app = FastAPI()

ws_protocol = "ws"
if os.environ.get("SSL") == "true":
    ws_protocol = "wss"

lock_1 = threading.Lock()


def load_empty_chunk():
    with open(os.path.join("res", "chunk_mov.webm"), "rb") as f:
        return f.read()


empty_chunk = load_empty_chunk()


class ChatManager:
    non_persistence_message_buffer = {}
    alt_member_list = {}
    current_blocked_member = set()
    possible_member_permission_on_channel = ["none", "accepted", "admin", "moderator", "blocked", "muted"]
    possible_member_status = ["idle", "active", "away", "busy"]
    possible_channel_state = ["inactive", "active", "unavailable"]
    message_format_template = {
        "sender": "string rw",
        "time": "string readonly",
        "message": "string rw",
        "deleted": "boolean",
        "edited": "boolean",
        "deleted_by": "",
        "seen_by": [],
        "received_by": []
    }

    def book_alt_name(self, alt_name, alt_key):
        if len(alt_name) >= 3 and type(alt_name) == str and type(alt_key) and len(alt_key) >= 8:
            if self.alt_member_list.get(alt_name) is None:
                self.alt_member_list[alt_name] = {"key": alt_key, "name": alt_name}
                return True
            else:
                return False
        else:
            return False

    def verify_alt_name(self, alt_name, alt_key):
        if self.alt_member_list.get(alt_name) is None:
            return False
        elif self.alt_member_list[alt_name]["key"] == alt_key:
            return True
        else:
            return False

    # channel_key is required to join the channel
    def new_channel(self, admin, admin_alt_key, channel_key, open_for_all=False):
        channel_id = str(uuid.uuid4())
        self.non_persistence_message_buffer[channel_id] = {}
        if self.alt_member_list.get(admin) is not None and self.alt_member_list[admin]["key"] == admin_alt_key:
            self.non_persistence_message_buffer[channel_id]["admin"] = admin
            self.non_persistence_message_buffer[channel_id]["channel_key"] = channel_key
            self.non_persistence_message_buffer[channel_id]["chats"] = []
            self.non_persistence_message_buffer[channel_id]["members"] = set()
            self.non_persistence_message_buffer[channel_id]["open_for_all"] = open_for_all
            self.non_persistence_message_buffer[channel_id]["closed"] = False
            self.non_persistence_message_buffer[channel_id]["tracker_publish"] = False
            self.non_persistence_message_buffer[channel_id]["members"].add(admin)
            return channel_id
        else:
            return None

    def store_chat(self, channel_id, sender_alt, sender_alt_key, message):
        if self.non_persistence_message_buffer.get(channel_id) is None:
            return False

        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                sender_alt in self.non_persistence_message_buffer[channel_id]["members"]):
            format_message = {
                "sender": sender_alt,
                "message": message,
                "time": str(datetime.datetime.now())
            }
            self.non_persistence_message_buffer[channel_id]["chats"].append(format_message)
            return True
        else:
            return False

    def get_chat_list(self, channel_id, sender_alt, sender_alt_key, index=0):
        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                sender_alt in self.non_persistence_message_buffer[channel_id]["members"]):
            return self.non_persistence_message_buffer[channel_id]["chats"][index:]
        else:
            return False

    def chat_last_index(self, channel_id, sender_alt, sender_alt_key):
        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                sender_alt in self.non_persistence_message_buffer[channel_id]["members"]):
            return len(self.non_persistence_message_buffer[channel_id]["chats"])
        else:
            return False

    def get_chat_by_index(self, channel_id, sender_alt, sender_alt_key, index):
        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                sender_alt in self.non_persistence_message_buffer[channel_id]["members"]):
            return self.non_persistence_message_buffer[channel_id]["chats"][index]
        else:
            return False

    # only chat owner and channel admin can delete chat
    def delete_chat(self, channel_id, sender_alt, sender_alt_key, message_index, deleter):
        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                (sender_alt == self.non_persistence_message_buffer[channel_id]["chats"][message_index]["sender"] or
                 sender_alt == self.non_persistence_message_buffer[channel_id]["admin"])):
            self.non_persistence_message_buffer[channel_id]["chats"][message_index]["deleted"] = True
            self.non_persistence_message_buffer[channel_id]["chats"][message_index]["deleted_by"] = deleter
        else:
            return False

    #
    def edit_chat(self, channel_id, sender_alt, sender_alt_key, message_index, message, editor):
        if (self.alt_member_list.get(sender_alt) is not None and
                self.alt_member_list[sender_alt]["key"] == sender_alt_key and
                sender_alt == self.non_persistence_message_buffer[channel_id]["chats"][message_index]["sender"]):
            if editor == self.non_persistence_message_buffer[channel_id][message_index]["sender"]:
                self.non_persistence_message_buffer[channel_id][message_index]["edited"] = True
                self.non_persistence_message_buffer[channel_id][message_index]["message"] = message

    def add_member_to_channel(self, channel_id, new_member, new_member_key=None, admin=None, admin_key=None):
        if self.non_persistence_message_buffer.get(channel_id) is None:
            return False

        if new_member is self.non_persistence_message_buffer[channel_id]["members"]:
            return True

        if new_member not in self.alt_member_list.keys():
            return False

        if (self.non_persistence_message_buffer[channel_id]["open_for_all"] and
                self.alt_member_list[new_member]["key"] == new_member_key):
            self.non_persistence_message_buffer[channel_id]["members"].add(new_member)
            return True
        elif (self.non_persistence_message_buffer[channel_id]["admin"] == admin and
              self.alt_member_list[admin]["key"] == admin_key):
            self.non_persistence_message_buffer[channel_id]["members"].add(new_member)
            return True
        else:
            return False

    def get_alt_name(self):
        return self.alt_member_list.keys()

    def open_channel_for_all(self, channel_id, admin, admin_key):
        if self.non_persistence_message_buffer.get(channel_id) is None:
            return False

        if (self.non_persistence_message_buffer[channel_id]["admin"] == admin and
                self.alt_member_list.get(admin) is not None and self.alt_member_list[admin]["key"] == admin_key):
            self.non_persistence_message_buffer[channel_id]["open_for_all"] = True
            return True
        else:
            return False

    def close_the_channel(self, channel_id, admin, admin_key):
        if self.non_persistence_message_buffer.get(channel_id) is None:
            return False

        if (self.non_persistence_message_buffer[channel_id]["admin"] == admin and
                self.alt_member_list.get(admin) is not None and self.alt_member_list[admin]["key"] == admin_key):
            self.non_persistence_message_buffer[channel_id]["closed"] = True
            return True
        else:
            return False

    def get_admin_all_channel(self, admin, admin_key):
        admin_channels = []
        print(self.non_persistence_message_buffer, self.alt_member_list, admin, admin_key)
        for channel_id in self.non_persistence_message_buffer.keys():
            if (self.non_persistence_message_buffer[channel_id]["admin"] == admin and
                    self.alt_member_list.get(admin) is not None and self.alt_member_list[admin]["key"] == admin_key):
                print(channel_id)
                admin_channels.append({
                    "channel": channel_id,
                    "open_for_all": self.non_persistence_message_buffer[channel_id]["open_for_all"],
                    "closed": self.non_persistence_message_buffer[channel_id]["closed"],
                    "members": self.non_persistence_message_buffer[channel_id]["members"]
                })
        print(admin_channels)
        return admin_channels

    def authenticate_alt_member(self, alt_name, alt_key):
        if self.alt_member_list.get(alt_name) is not None and self.alt_member_list[alt_name]["key"] == alt_key:
            return True
        else:
            return False


class WebsocketManager:

    def __init__(self, cm):
        self.active_connection = {}
        self.chat_manager = cm

    def connect(self, websocket):
        self.active_connection[websocket] = {}

    async def sync_chat(self, websocket, channel_id, alt_name, alt_pass, init, message=""):
        if init:
            till_now_chats = self.chat_manager.get_chat_list(channel_id, alt_name, alt_pass)
            self.active_connection[websocket]["index"] = len(till_now_chats)
            self.active_connection[websocket]["channel_id"] = channel_id
            for chat_by_one in till_now_chats:
                await websocket.send_json(chat_by_one)
        else:
            # not initialized than somebody send chat message then next is check all the web socket related for
            # this channel and send the corresponding message
            chat_manager.store_chat(channel_id, alt_name, alt_pass, message)
            self.active_connection[websocket]["index"] += 1
            for ws in self.active_connection.keys():
                if self.active_connection[ws]["channel_id"] == channel_id and ws != websocket:
                    index = self.active_connection[ws]["index"]
                    previous_sync_till_now = self.chat_manager.get_chat_list(channel_id, alt_name, alt_pass, index)
                    self.active_connection[ws]["index"] = index + len(previous_sync_till_now)
                    for chat_by_one in previous_sync_till_now:
                        await ws.send_json(chat_by_one)

    def disconnect(self, websocket):
        del self.active_connection[websocket]


class VideoStreamingWebSocketManager:

    def __init__(self, vc):
        self.active_connection = {}
        self.stream_buffer = {}
        self.video_conference: VideoConference = vc

    def connect(self, websocket, channel_id, streamer_id):
        self.active_connection[websocket] = {
            "channel_id": channel_id,
            "streamer_id": streamer_id
        }
        if self.stream_buffer.get(channel_id) is None:
            self.stream_buffer[channel_id] = {}

    def is_any_streamer_alive_on_channel(self, channel_id):
        for ws in self.active_connection.keys():
            if self.active_connection[ws]["channel_id"] == channel_id:
                return True
        return False

    def get_live_streamers_on_channel(self, channel_id):
        # (c, l_) = self.sync_write_stream_buffer("ls_streamer", channel_id, None)
        # return c
        if self.stream_buffer.get(channel_id) is not None:
            return list(self.stream_buffer[channel_id].keys())
        else:
            return []

    def get_my_ws_channel_streamer(self, ws):
        channel_id = self.active_connection[ws]["channel_id"]
        return self.get_live_streamers_on_channel(channel_id)

    # def sync_write_stream_buffer(self, action, channel_id, streamer_id, chunk=None):
    #     c = empty_chunk
    #     l_ = 0
    #     print("enter", action, channel_id, streamer_id)
    #     lock_1.acquire()
    #     print("locked", action, channel_id, streamer_id)
    #     if action == "chunk":
    #         self.stream_buffer[channel_id][streamer_id].append(chunk)
    #         l_ = len(self.stream_buffer[channel_id][streamer_id])
    #     elif action == "sl":    # shift left
    #         if self.stream_buffer.get(channel_id) is None or self.stream_buffer[channel_id].get(streamer_id) is None:
    #             l_ = None
    #         else:
    #             l_ = len(self.stream_buffer[channel_id][streamer_id])
    #             if l_ > 0:
    #                 c = self.stream_buffer[channel_id][streamer_id].popleft()
    #     elif action == "len":
    #         l_ = len(self.stream_buffer[channel_id][streamer_id])
    #     elif action == "init":
    #         self.stream_buffer[channel_id][streamer_id] = deque()
    #     elif action == "ls_streamer":
    #         if self.stream_buffer.get(channel_id) is not None:
    #             c = list(self.stream_buffer[channel_id].keys())
    #         else:
    #             c = []
    #     else:
    #         pass
    #     lock_1.release()
    #     print("released", action, channel_id, streamer_id, l_)
    #     return c, l_

    async def streamed_video_conference(self, websocket, chunk):
        channel_id = self.active_connection[websocket]["channel_id"]
        streamer_id = self.active_connection[websocket]["streamer_id"]
        # self.sync_write_stream_buffer("chunk", channel_id, streamer_id, chunk)
        self.stream_buffer[channel_id][streamer_id] = chunk
        return True

    def get_chunk_of_channel(self, channel, streamer):
        while True:
            if self.stream_buffer.get(channel) is None or self.stream_buffer[channel].get(streamer) is None:
                # yield b"--frame--"
                break
            # frames = iio.imread(self.stream_buffer[channel][streamer], index=None, format_hint=".webm")
            # delays = 1.0/float(len(frames))
            # for frame in frames:
            #    yield b"--frame\\r\\n" b"Content-Type: video/webm\r\r\r\r" + frame + b"\r\n"
            yield self.stream_buffer[channel][streamer]
            asyncio.sleep(1.0)

    # This will automatically trigger when server or client close the connection through the exception
    def disconnect(self, websocket):
        channel_id = self.active_connection[websocket]["channel_id"]
        streamer_id = self.active_connection[websocket]["streamer_id"]
        del self.stream_buffer[channel_id][streamer_id]
        del self.active_connection[websocket]

    # explicitly websocket close all the active connection
    def end_all_stream_of_channel(self, channel_id, organiser, organiser_password):
        if (self.video_conference.chat_manager.authenticate_alt_member(organiser, organiser_password)
                and self.video_conference.channels[channel_id]["host"] == organiser):
            for ws in self.active_connection.keys():
                if self.active_connection[ws]["channel_id"] == channel_id:
                    ws.close()
            return True
        else:
            return False


class VideoConference:
    channels = {}

    def __init__(self, chat1_manager):
        self.chat_manager: ChatManager = chat1_manager

    def create_channel(self, organiser, organiser_password):
        if self.chat_manager.authenticate_alt_member(organiser, organiser_password):
            channel_id = str(uuid.uuid4())
            self.channels[channel_id] = {}
            self.channels[channel_id]["host"] = organiser
            self.channels[channel_id]["members"] = set()
            self.channels[channel_id]["members"].add(organiser)
            # this streamer count as per request join
            self.channels[channel_id]["streamer_count"] = 0
            self.channels[channel_id]["streamers"] = {}
            return channel_id
        else:
            return None

    def add_member(self, member, channel_id, organiser, organiser_password):
        if (self.chat_manager.authenticate_alt_member(organiser, organiser_password)
                and self.channels[channel_id]["host"] == organiser and
                self.chat_manager.alt_member_list.get(member) is not None):
            self.channels[channel_id]["members"].add(member)
            return True
        else:
            return False

    def remove_member(self, member, channel_id, organiser, organiser_password):
        if (self.chat_manager.authenticate_alt_member(organiser, organiser_password)
                and self.channels[channel_id]["host"] == organiser):
            self.channels[channel_id]["members"].remove(member)

    # only member can join stream would share authentication
    def request_stream_id(self, channel_id, member, member_password):
        if (self.chat_manager.authenticate_alt_member(member, member_password) and
                member in self.channels[channel_id]["members"]):
            self.channels[channel_id]["streamer_count"] += 1
            if self.channels[channel_id]["streamers"].get(member) is None:
                stream_id = str(uuid.uuid4())
                self.channels[channel_id]["streamers"][member] = stream_id
            return self.channels[channel_id]["streamers"][member]
        else:
            return None

    def get_admin_all_channel(self, host, host_key):
        admin_channels = []
        print(self.channels, host, host_key)
        for channel_id in self.channels.keys():
            if (self.channels[channel_id]["host"] == host and
                    self.chat_manager.alt_member_list.get(host) is not None and
                    self.chat_manager.alt_member_list[host]["key"] == host_key):
                admin_channels.append({
                    "channel": channel_id,
                    "open_for_all": False,
                    "closed": False,
                    "members": self.channels[channel_id]["members"]
                })
        print(admin_channels)
        return admin_channels


chat_manager = ChatManager()
video_conference = VideoConference(chat_manager)
websocket_manager = WebsocketManager(chat_manager)
stream_ws_manager = VideoStreamingWebSocketManager(video_conference)


@app.websocket("/ws_v2")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            print(data_json)
            if data_json["action"] == "close":
                await websocket.close()
                websocket_manager.disconnect(websocket)
                break
            elif data_json["action"] == "init":
                await websocket_manager.sync_chat(
                    websocket, data_json["channel_id"], data_json["alt_name"], data_json["alt_pass"], True)
            elif data_json["action"] == "continue":
                await websocket_manager.sync_chat(
                    websocket, data_json["channel_id"], data_json["alt_name"], data_json["alt_pass"], False,
                    data_json["message"])
            else:
                await websocket.send_json({"Error": "Error"})
    except (WebSocketDisconnect, ConnectionClosed) as rrr:
        print("Exception capture on websocket connection", rrr)
        websocket_manager.disconnect(websocket)


@app.get("/ui_v2")
def bot_ui(response_class=PlainTextResponse):
    with open(os.path.join("ui", "chat_ui_v2.template"), "r") as f:
        initial_ui = Template(
            f.read()).render(
            proto=ws_protocol,
            wss_port=os.environ["WSS_PORT"],
            wss_host=os.environ["WSS_HOST"]
        )
        initial_ui = initial_ui
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response


@app.post("/alt_manager")
async def alt_manager(request: Request):
    body = await request.json()
    # {initiate: True, persona: "", "bot_response": ""}
    print(body, type(body))
    if body.get("action") == "link":
        return {"result": chat_manager.verify_alt_name(body.get("alt_login_name"), body.get("alt_login_pass"))}
    elif body.get("action") == "create":
        return {"result": chat_manager.book_alt_name(body.get("alt_login_name"), body.get("alt_login_pass"))}
    else:
        return {"result": False}


@app.post("/channel_adminer")
async def channel_adminer(request: Request):
    body = await request.json()
    # {initiate: True, persona: "", "bot_response": ""}
    if body.get("action") == "create":
        return {"channel_id": chat_manager.new_channel(
            body.get("alt_login_name"), body.get("alt_login_pass"), body.get("channel_key"), body.get("open")
        )}
    elif body.get("action") == "joiner":
        if body.get("admin") is None:
            return {"result": chat_manager.add_member_to_channel(
                body.get("channel_id"), body.get("alt_login_name"), body.get("alt_login_pass")
            )}
        else:
            return {"result": chat_manager.add_member_to_channel(
                body.get("channel_id"), body.get("alt_login_name"), body.get("admin"), body.get("admin_key")
            )}
    elif body.get("action") == "open_for_all":
        return {"result": ""}
    elif body.get("action") == "add_member":
        return {"result": chat_manager.add_member_to_channel(body.get("channel_id"), body.get("admin"), body.get("admin_key"))}
    elif body.get("action") == "close_channel":
        return {"result": ""}
    elif body.get("action") == "fetch_admin_ui":
        with open(os.path.join("ui", "channel_admin.template"), "r") as f:
            initial_ui = Template(
                f.read()).render(
                channels=chat_manager.get_admin_all_channel(body.get("admin"), body.get("admin_key"))
            )
        return {"result": initial_ui}
    else:
        return {"result": None}


# ================ Video/Audio test =======================
@app.websocket("/ws_video_test")
async def websocket_video_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            await websocket.send_bytes(data)
    except (WebSocketDisconnect, ConnectionClosed) as rrr:
        print("Exception capture on websocket connection", rrr)


@app.get("/video_ui_test")
def video_ui(response_class=PlainTextResponse):
    with open(os.path.join("ui", "video_stream_test_ui.template"), "r") as f:
        initial_ui = Template(
            f.read()).render(
            proto=ws_protocol,
            wss_port=os.environ["WSS_PORT"],
            wss_host=os.environ["WSS_HOST"]
        )
        initial_ui = initial_ui
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response


# ================ Video/Audio Conference =======================

@app.websocket("/ws_video_v2/{channel}/{streamer}")
async def websocket_video_stream_endpoint(channel: str, streamer: str, websocket: WebSocket):
    await websocket.accept()
    stream_ws_manager.connect(websocket, channel, streamer)
    try:
        while True:
            data = await websocket.receive_bytes()
            await stream_ws_manager.streamed_video_conference(websocket, data)

            # response the stream
            related_streamers = stream_ws_manager.get_my_ws_channel_streamer(websocket)
            # await asyncio.sleep(1)
            await websocket.send_json(
                {"streamer_count": len(related_streamers), "live_streamer": related_streamers})
    except (WebSocketDisconnect, ConnectionClosed) as rrr:
        stream_ws_manager.disconnect(websocket)
        print("Exception capture on websocket connection", rrr)


@app.get("/conference_ui_v2")
def conference_ui(response_class=PlainTextResponse):
    with open(os.path.join("ui", "video_chat_ui.template"), "r") as f:
        initial_ui = Template(
            f.read()).render(
            proto=ws_protocol,
            wss_port=os.environ["WSS_PORT"],
            wss_host=os.environ["WSS_HOST"]
        )
        initial_ui = initial_ui
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response


@app.post("/conference_manage")
async def conference_api(request: Request):
    body = await request.json()
    # create channel
    # {initiate: True, persona: "", "bot_response": ""}
    if body.get("action") == "create_channel":
        return {"channel_id": video_conference.create_channel(body.get("alt_login_name"), body.get("alt_login_pass"))}

    # request stream for a member of particular channel
    if body.get("action") == "request_stream":
        return {"streaming_id": video_conference.request_stream_id(
            body.get("channel_id"), body.get("alt_login_name"), body.get("alt_login_pass"))}

    # add member to channel
    if body.get("action") == "add_member":
        return {"result": video_conference.add_member(
            body.get("member"), body.get("channel_id"), body.get("alt_login_name"), body.get("alt_login_pass"))}

    # add member to channel
    if body.get("action") == "remove_member":
        return {"result": video_conference.remove_member(
            body.get("member"), body.get("channel_id"), body.get("alt_login_name"), body.get("alt_login_pass"))}

    # authenticate member
    # It is already provided by chat manager hence not required

    # end all stream
    if body.get("action") == "end_all_stream":
        return {"result": stream_ws_manager.end_all_stream_of_channel(
            body.get("channel_id"), body.get("alt_login_name"), body.get("alt_login_pass"))}

    if body.get("action") == "fetch_admin_ui":
        with open(os.path.join("ui", "channel_admin.template"), "r") as f:
            initial_ui = Template(
                f.read()).render(
                channels=video_conference.get_admin_all_channel(body.get("alt_login_name"), body.get("alt_login_pass"))
            )
        return {"result": initial_ui}

    return {"result": None}


@app.get("/broadcast_v2/{channel}/{streamer}")
async def broadcaster_channel(channel: str, streamer: str):
    chunk = await run_in_threadpool(stream_ws_manager.get_chunk_of_channel, channel, streamer)
    return StreamingResponse(chunk, media_type="multipart/x-mixed-replace;boundary=frame")

# ============= Video streaming behavior test====================


@app.get("/test/video")
async def broadcaster_channel():
    return {"result": None}

# ============= (Deprecated) Old reply UI for chatbot design =================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if data == "stop":
            await websocket.send_json({"response": "Bye"})
        else:
            for message in ["hello", "what do you want", "blah", "blah blahh"]:
                await websocket.send_json({"response": message})


@app.get("/ui")
def bot_ui(response_class=PlainTextResponse):
    with open(os.path.join("ui", "chat_ui.template"), "r") as f:
        initial_ui = Template(
            f.read()).render(
            data=[{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}],
            wss_port=os.environ["WSS_PORT"]
        )
        initial_ui = initial_ui
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response


@app.post("/bot")
async def bot_query(request: Request):
    body = await request.json()
    print(body, type(body))
    # {query: "query"}
    return {"response": "Hello"}


@app.post("/persona_simulator_query")
async def custom_next_query(request: Request):
    body = await request.json()
    # {initiate: True, persona: "", "bot_response": ""}
    print(body, type(body))
    if body.get("initiate"):
        return {"query": "hello"}
    else:
        return {"query": "bye", "intent": "halt"}


@app.get("/persona_ui")
def persona_ui(response_class=PlainTextResponse):
    with open(os.path.join("ui", "persona_form.template"), "rb") as f:
        initial_ui = f.read()
        initial_ui = initial_ui
    response = Response(content=initial_ui)
    response.headers["content-type"] = "text/html"
    return response


@app.post("/create_agent")
async def create_agent(request: Request):
    body = await request.json()
    # {name: "", "age": "", "role": "", "occupation": "", "needs": "", "behavior": ""}
    print(body, type(body))
    return {"message": "ok"}


# ============== Start the server
if os.environ.get("SSL") == "true":
    # import ssl
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain(, keyfile=)
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_certfile=os.path.join("cer", "main.cer"), ssl_keyfile=os.path.join(
        "cer", "main.key"))
else:
    uvicorn.run(app, host="0.0.0.0", port=8000)
