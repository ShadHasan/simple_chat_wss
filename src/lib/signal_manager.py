import uuid
import datetime

class SignalManager:

    candidate_socket_map = {}
    """
    {
        <ws>: {
            "<pc_uuid>": {
                "access": "public/private",
                "pc_uuid": "<>",
                "candidate": <candidate>,
                "altname": "",
                "client_type": "end/service",
                "register_time": ""
            }
        }
    }
    """
    
    # below is to main uniqueness of pc_uuid across all the websocket
    # It will be "static" hence will not shared with instance.
    allocate_pc_uuid = {}
    
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
        
        
    def initPeerConnectionUUID(self, data):
        data["pc_uuid"] = str(uuid.uuid4())
        SignalManager.allocate_pc_uuid[data["pc_uuid"]] = {
            "ws": data["websocket"], "altname": data["altname"]}
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "pc_initiated_uuid"
        return data
        

    def register_websocket_candidate(self, data):
        try:
            if candidate_socket_map.get(data["websocket"]) is None:
            
                candidate_socket_map[data["websocket"]] = {
                    data["pc_uuid"]: {
                        "candidate": data["candidate"],
                        "altname": SignalManager.allocate_pc_uuid[pc_uuid]["altname"],
                        "client_type": data["client_type"],
                        "register_time": datetime.datetime.now()
                    }
                }
            else:
                candidate_socket_map[data["websocket"]][data["pc_uuid"]] = {
                    "candidate": data["candidate"],
                    "altname": SignalManager.allocate_pc_uuid[pc_uuid]["altname"],
                    "client_type": data["client_type"],
                    "register_time": datetime.datetime.now()
                }
            
            data["status"] = "ok"
        except:
            data["status"] = "nok"
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
            candidate = candidate_socket_map[SignalManager.allocate_pc_uuid[pc_uuid]["ws"]][pc_uuid]["candidate"]
        except Exception as e:
            print("Exception occured in fetching candidate: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "altname_candidate"
        data["candidates"] = candidate
        return data
        
    async def forward_signal_to(self, data):
        try:
            forwarding_wss = {}
            if data["directive"] == "forward_offer":
                data["directive"] = "incoming_offer"
                to_altname = data["to_altname"]
                for pc_uuid in SignalManager.allocate_pc_uuid.keys():
                    if SignalManager.allocate_pc_uuid[pc]["altname"] == to_altname:
                        data["answer_pc_uuid"] = pc_uuid
                        await SignalManager.allocate_pc_uuid[pc]["ws"].send_json(data)
                signal_response = "fowarded_offer"
            elif data["directive"] == "forward_answer":
                data["directive"] = "incoming_answer"
                await SignalManager.allocate_pc_uuid[data["offer_pc_uuid"]]["ws"].send_json(data)
                signal_response = "fowarded_answer"
            
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
            print("Exception occured in fetching candidate: {}".format(e))
            status = "nok"
        del data["directive"]
        del data["websocket"]
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
        
        
    def signal_directive_switch(self, websocket, data):
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
                "call": self.forward_signal_to
            },
            "forward_answer": {
                "call": self.forward_signal_to
            },
            "forward_network_request": {
                "call": self.forward_signal_to
            },
            "forward_network_request_response": {
                "call": self.forward_signal_to
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
        return signal_processor[data["directive"]]["call"](data)
		
	