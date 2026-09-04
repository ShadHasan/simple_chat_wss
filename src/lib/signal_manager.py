import uuid
import asyncio
import datetime

class SignalManager:

    socket_altname = {}
    """
    {
        <ws>: <altname>
    }
    """
    
    # below is to main uniqueness of pc_uuid across all the websocket
    # It will be "static" hence will not shared with instance.
    allocate_pc_uuid = {}
    """
    {
        "<pc_uuid>": {
            "type": "1-to-1",
            "offer_party": {
                "websocket": websocket
                "altname": "<altname>",
                "candidate": "",
                "client_type": "end",  # It is always end type.
                "register_time": ""
            },
            "answer_party": {
                "altname": "<altname>",
                "candidate": "",
                "websocket": None(initial),
                "client_type": "end/service", # It could be end type or service client. 
                "register_time": ""
            }
        }
    }
    """
    
    chat_rooms = {}
    """
    {
        "room_uuid": {
            "name": "",
            "access": "public/private",
            "member_altname": []
        }
    }
    """
    
    email_to_altname = {}
    """
    email_to_altname is generally used for authentication.
    
    Note: altname is unique assigned, cannot be allocated same altname to multiple email.
    But an email can have multiple altnames.
    {
        "<email>": ["<altname_1>":,"<altname_3>", ...]
        "<email2>": ["<altname_2>":,"<altname_4>", ...]
    }
    """
    
    all_altnames = {}
    """
    {
        "<altname_1>": {"networks": [<altname>...], "access": "public/private"},
        "<altname_3>": ...
    }
    """
    
    """
    Key Fact:
    Note: altname_1 could be altname_1 which mean altname_1@localhost, or to be with
        specific domain i.e. altname_1@example.com
        
        however which signal server tied to its one domain or aliases. 
        Hence key of all_altnames belongs these domain only.
        However networks of any altname this domains can keep with other domain.
        But for communication signal need to send to other domain.
        
    """
	
    
    def __init__(self):
        # load email_altname from database
        self.all_altnames = {
            "altname_1" : {
                "networks": ["altname_4", "altname_7"], "access": "public"
            },
            "altname_2": {
                "networks": [], "access": "private"
            },
            "altname_3": {
                "networks": ["altname_4"], "access": "private"
            },
            "altname_4" : {
                "networks": ["altname_7"], "access": "public"
            },
            "altname_5": {
                "networks": ["altname_6", "altname_4", "altname_7"], "access": "private"
            },
            "altname_6" : {
                "networks": ["altname_2", "altname_4", "altname_7"], "access": "private"
            },
            "altname_7": {
                "networks": ["altname_6", "altname_4", "altname_3"], "access": "private"
            },
        }
        
    def iam(self, data):
        # Here we need to validate/authenticate for altname
        self.socket_altname[data["websocket"]] = data["altname"]
        data["signal_response"] = "socket_mapped"
        del data["directive"]
        del data["websocket"]
        return data
        
        
    def initPeerConnectionUUID(self, data):
        # Here we need to validate/authenticate for altname
        data["pc_uuid"] = str(uuid.uuid4())
        SignalManager.allocate_pc_uuid[data["pc_uuid"]] = {
            "type": "1-to-1",
            "offer_party": {
                "websocket": data["websocket"],
                "altname": data["altname"],
                "ldp_sdp": None,
                "candidate": None
            },
            "answer_party": {
                "altname": None,
                "candidate": None,
                "ldp_sdp": None,
                "websocket": None
            }
        }
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "pc_initiated_uuid"
        return data
        

    def register_websocket_candidate(self, data):
        try:
            if data["party"] == "answer_party":
                if SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]].get("websocket") is None:
                    SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]]["websocket"] = data["websocket"]
                    
                else:
                    data["error"] = "already responded by other client"
                    raise RuntimeError("already responded")
            SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]]["candidate"] = data["candidate"]
            SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]]["ldp_sdp"] = data["sdp"]
            data["status"] = "ok"
        except Exception as e:
            data["status"] = "nok"
            data["error"] = str(e)
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "registered_candidate"
        return data
        
        
    def get_public_altname(self, data):
        altnames = []
        try:
            for altname in self.all_altnames.keys():
                if self.all_altnames[altname]["access"] == "public":
                    altnames.append(altname)
        except Exception as e:
            print("Exception occured in fetching public altnames: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "public_altnames"
        data["public_altnames"] = altnames
        return data
        
    def get_my_altname_networks(self, data):
        altnames = []
        try:
            altnames = all_altnames[data[my_altname]]["networks"]
        except Exception as e:
            print("Exception occured in fetching networks altnames in my altname: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "networks_altnames"
        data["networks_altnames"] = altnames
        return data
        
    def get_candidate_by_pc_uuid(self, data):
        candidate = None
        try:
            pc_uuid = data["pc_uuid"]
            party = data["party"]
            
            candidate = SignalManager.allocate_pc_uuid[pc_uuid][party]["candidate"]
            sdp = SignalManager.allocate_pc_uuid[pc_uuid][party]["ldp_sdp"]
            signal_response = "pc_candidate"
        except Exception as e:
            signal_response = "generic_error"
            data["error"] = "Exception occured in fetching candidate: {}".format(e)
            print(data["error"])
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = signal_response
        data["candidate"] = candidate
        data["sdp"] = sdp
        return data
        
    async def forward_signal_to(self, data):
        try:
            forwarding_wss = {}
            if data["directive"] == "forward_offer":
                forwarded = False
                data["signal_response"] = "incoming_offer"
                data["from_altname"] = SignalManager.allocate_pc_uuid[data["pc_uuid"]]["offer_party"]["altname"]
                data["sdp"] = SignalManager.allocate_pc_uuid[data["pc_uuid"]]["offer_party"]["ldp_sdp"]
                to_altname = data["to_altname"]
                for ws in self.socket_altname.keys():
                    if self.socket_altname[ws] == to_altname:
                        forwarded = True
                        SignalManager.allocate_pc_uuid[data["pc_uuid"]]["answer_party"]["altname"] = to_altname
                        if data.get("websocket") is not None:  del data["websocket"]
                        await ws.send_json(data)
                signal_response = "forwarded_offer"
                if not forwarded:
                    data["error"] = "Offer failed, altname is not online {}".format(to_altname)
                    raise RuntimeError("altname is not online")
            elif data["directive"] == "forward_answer":
                data["signal_response"] = "incoming_answer"
                pc_uuid = data["pc_uuid"]
                
                if SignalManager.allocate_pc_uuid[pc_uuid]["answer_party"]["websocket"] == data["websocket"]:
                    from_altname = SignalManager.allocate_pc_uuid[pc_uuid]["answer_party"]["altname"]
                    to_altname = SignalManager.allocate_pc_uuid[pc_uuid]["offer_party"]["altname"]
                    del data["websocket"]
                    data["sdp"] = SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]]["ldp_sdp"]
                    data["candidate"] = SignalManager.allocate_pc_uuid[data["pc_uuid"]][data["party"]]["candidate"]
                    await SignalManager.allocate_pc_uuid[pc_uuid]["offer_party"]["websocket"].send_json(data)
                    if not data["offer_accepted"]:
                        del SignalManager.allocate_pc_uuid[pc_uuid]
                    signal_response = "fowarded_answer"
                else:
                    signal_response = "fowarded_answer"
                    data["error"] = "Illegal answer"
                    raise RuntimeError("already responded")
                
            
            elif data["directive"] == "forward_network_request":
                to_altname = data["to_altname"]
                from_altname = SignalManager.allocate_pc_uuid[data["pc_uuid"]]["altname"]
                data["from_altname"] = from_altname
                del data["to_altname"]
                data["directive"] = "incoming_network_request"
                
                for pc_uuid in SignalManager.keys():
                    if SignalManager[pc_uuid]["altname"] == to_altname:
                        await SignalManager.allocate_pc_uuid[data[pc_uuid]]["ws"].send_json(data)
                signal_response = "fowarded_network_request"
            
            elif data["directive"] == "forward_network_request_response":
                to_altname = data["to_altname"]
                from_altname = SignalManager.allocate_pc_uuid[data["pc_uuid"]]["altname"]
                data["directive"] = "incoming_network_request_response"
                if (data["network_request"] == "accepted"):
                    if from_altname not in all_altnames[to_altname]["networks"]:
                        all_altnames[to_altname]["networks"].appends(from_altname)
                    if to_altname not in all_altnames[from_altname]["networks"]:
                        all_altnames[from_altname]["networks"].appends(to_altname)
                for pc_uuid in SignalManager.keys():
                    if SignalManager[pc_uuid]["altname"] == to_altname:
                        await SignalManager.allocate_pc_uuid[data[pc_uuid]]["ws"].send_json(data)
                signal_response = "fowarded_network_request_response"
                
            status = "ok"
        except Exception as e:
            status = "nok"
            signal_response = "generic_error"
            data["error"] = "Exception occured in {}: {}".format(data["directive"], e)
            print(data["error"])
            
        del data["directive"]
        if data.get("websocket"):  del data["websocket"]
        data["signal_response"] = signal_response
        data["status"] = status
        return data
        
    # Deprecated
    def get_current_websocket_requested_altnames(self, data):
        requested_altnames = []
        try:
            requested_altnames = candidate_socket_map[data["websocket"]]["requested_altnames"]
        except Exception as e:
            print("Exception occured in requested_altnames: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "my_candidate_shared_to_altnames"
        data["requested_altnames"] = requested_altnames
        return data
        
    def update_my_altname_access(self, data):
        status = "nok"
        try:
            altname = candidate_socket_map[data["websocket"]][data["pc_uuid"]]["altname"]
            if data["access"] in ["public", "private"]:
                all_altnames[altname]["access"] = data["access"]
                status = "ok"
            else:
                raise RuntimeError("access is unknown, {}".format(data["access"]))
        except Exception as e:
            status = "nok"
            print("Exception occured in requested_altnames: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "access_updated"
        data["status"] = status
        return data
        
        
    async def signal_directive_switch(self, websocket, data):
        # Please note: if signal socket gone, simply candidate is loss. Hence
        # client has to connect signal socket and register candidate to its
        # signal socket.
        """
        signal_response = {
            "register_candidates": "{registered_candidate: ok/nok}",
            "forward_offer": "{forwarded_offer: ok/nok, to_altname: <altname>}",
            "forward_answer": "{forwarded_answer: ok/nok, to_altname: <altname>}",
            "my_websocket_requested_altnames": "{my_candidate_shared_to_altnames: [<altname>...]}",
            "forward_network_request": "forwarded_network_request: {status: ok/nok, to_altname: <altname>}",
            "forward_network_request_response": "forwarded_network_request_response: {status: accepted/rejected, by_altname: <altname>}",
            "public_altname": "{public_altnames: [<altname>...]}",
            "request_candidate": "{altname: <altname>, candidate: <candidate of altname>/None}",
            "update_my_altname_access": "{access_updated: ok/nok}"
        }
        """
        
        signal_processor = {
            "my_altname": {
                "call": self.iam
            },
            "pc_init_uuid": {
                "call": self.initPeerConnectionUUID
            },
            "register_candidates": {
                "call":  self.register_websocket_candidate
            },
            "request_candidate": {
                "call": self.get_candidate_by_pc_uuid
            },
            "forward_offer": {
                "call": self.forward_signal_to,
                "type": "async"
            },
            "forward_answer": {
                "call": self.forward_signal_to,
                "type": "async"
            },
            "forward_network_request": {
                "call": self.forward_signal_to,
                "type": "async"
            },
            "forward_network_request_response": {
                "call": self.forward_signal_to,
                "type": "async"
            },
            "public_altname": {
                "call": self.get_public_altname
            },
            "update_my_altname_access": {
                "call": self.update_my_altname_access
            },
            "get_my_networks": {
                "call": self.get_my_altname_networks
            }
        }
        data["websocket"] = websocket
        if signal_processor[data["directive"]].get("type") == "async":
            return await signal_processor[data["directive"]]["call"](data)
        else:
            return signal_processor[data["directive"]]["call"](data)
		
	