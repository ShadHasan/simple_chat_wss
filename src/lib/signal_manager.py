import datetime

class SignalManager:

	candidate_socket_map = {}
    """
	{
		<ws>: {
			"access": "public/private",
			"candidate": <candidate>,
			"altname": "",
            "client_type": "end/service",
            "register_time": "",
            "requested_altnames": []
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
    {
        "<email>": [
            {"<altname_1>": {"network": [<altname>...]},
            {"<altname_3>": ...}
        ]
    }
    """
	
    
    def __init__(self):
        pass
        # load email_altname from database

	def register_websocket_candidate(self, data):
        try:
            candidate_socket_map[data["websocket"]] = {
                "candidate": data["candidate"],
                "altname": data["altname"],
                "client_type": data["client_type"],
                "register_time": datetime.datetime.now(),
                "access": data["access"] if data.get("access") is not None else "private",
                "requested_altnames": set()
            }
            del data["directive"]
            del data["websocket"]
            data["signal_response"] = "registered_candidate"
            data["status"] = "ok"
        except:
            del data["directive"]
            del data["websocket"]
            data["signal_response"] = "registered_candidate"
            data["status"] = "nok"
        return data
        
        
    def get_public_altname(self, data):
        altnames = []
        try:
            for ws in candidate_socket_map.key():
                if candidate_socket_map[ws]["access"] == data["public"]:
                    altnames.append(candidate_socket_map[ws]["altname"])
        except Exception as e:
            print("Exception occured in fetching public altnames: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "public_altnames"
        data["public_altnames"] = altnames
        return data
        
    def get_candidate_by_altname(self, data):
        candidates = []
        try:
            for ws in candidate_socket_map.key():
                if candidate_socket_map[ws]["altname"] == data["altname"]:
                    candidate.append(candidate_socket_map[ws]["candidate"])
                    candidate_socket_map[ws]["requested_altnames"].add(data["from_altname"])
        except Exception as e:
            print("Exception occured in fetching candidate: {}".format(e))
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = "altname_candidates"
        data["candidates"] = candidates
        return data
        
    async def forward_signal_to(self, data):
        try:
            from_altname = data["from_altname"]
            to_altname = data["to_altname"]
            transaction_id = data["transaction_id"]
            forward_payload = data["forward_payload"]
            
            if data["directive"] = "forward_offer":
                signal_response = "fowarded_offer"
            elif data["directive"] == "forward_answer":
                signal_response = "fowarded_answer"
            
            elif data["directive"] == "forward_network_request":
                signal_response = "fowarded_network_request"
            
            elif data["directive"] == "forward_network_request_response":
                signal_response = "fowarded_network_request_response"
            
        
            for ws in candidate_socket_map.key():
                if candidate_socket_map[ws]["altname"] == to_altname:
                    await ws.send_json(data)
            status = "ok"
        except Exception as e:
            print("Exception occured in fetching candidate: {}".format(e))
            status = "nok"
        del data["directive"]
        del data["websocket"]
        data["signal_response"] = signal_response
        data["status"] = status
        return data
        
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
        status = "ok"
        try:
            for ws in candidate_socket_map.key():
                if candidate_socket_map[ws]["altname"] == data["altname"]:
                    candidate_socket_map[ws]["access"] = data["access"]
            status = "ok"
        except Exception as e:
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
            "register_candidates": {
                "call":  register_websocket_candidate,
            },
            "forward_offer": {
                "call": forward_signal_to,
            },
            "forward_answer": {
                "call": forward_signal_to,
            },
            "my_websocket_requested_altnames": {
                "call": get_current_websocket_requested_altnames,
            },
            "forward_network_request": {
                "call": forward_signal_to,
            },
            "forward_network_request_response": {
                "call": forward_signal_to,
            },
            "public_altname": {
                "call": get_public_altname,
            },
            "request_candidate": {
                "call": get_candidate_by_altname,
            },
            "update_my_altname_access": {
                "callback": update_my_altname_access,
            }
        }
        data["websocket"] = websocket
        
        await websocket.send_json(signal_processor[data["directive"]]["call"](data))
		
	