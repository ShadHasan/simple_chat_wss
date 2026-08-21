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
                "access": data["access"] if data.get("access") is not None else "private"
            }
            return {"registered_candidate": "ok"}
        except:
            return {"registered_candidate": "nok"}
        
        
    def get_public_altname_candidate(self):
        pass
        
    def get_candidate_by_altname(self, websocket, altname):
        pass
        
    def forward_signal_to(self, altname, signal_data):
        pass
        
    def get_current_websocket_requested_altnames(self, websocket):
        pass
        
    def update_my_altname_access(self, altname, access):
        pass
        
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
                "call": get_public_altname_candidate,
            },
            "request_candidate": {
                "call": get_candidate_by_altname,
            },
            "update_my_altname_access": {
                "callback": update_my_altname_access,
            }
        }
        data[websocket] = websocket
        
        await websocket.send_json(signal_processor[data["directive"]]["call"](data))
		
	