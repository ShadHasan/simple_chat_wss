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

	def register_websocket_candidate(self, websocket, email, candidate, altname, client_type, access=private):
        pass
        
    def get_public_altname_candidate(self):
        pass
        
    def get_candidate_by_altname(self, websocket, altname):
        pass
        
    def forward_signal_to(self, altname, signal_data):
        pass
        
    def get_current_websocket_requested_altnames(self, websocket):
        pass
        
    async def signal_directive_switch(self, websocket, data):
        # Please note: if signal socket gone, simply candidate is loss. Hence
        # client has to connect signal socket and register candidate to its
        # signal socket.
        signal_response = {
            "register_candidates": "{registered_candidate: ok/nok}",
            "forward_offer": "{forwarded_offer: ok/nok, to_altname: <altname>}",
            "forward_answer": "{forwarded_answer: ok/nok, to_altname: <altname>}",
            "my_websocket_requested_altnames": "{my_candidate_shared_to_altnames: [<altname>...]}",
            "forward_network_request": "forwarded_network_request: {status: ok/nok, to_altname: <altname>}",
            "forward_network_request_response": "forwarded_network_request_response: {status: accepted/rejected, by_altname: <altname>}",
            "public_altname": "{public_altnames: [<altname>...]}",
            "request_candidate": "{altname: <altname>, candidate: <candidate of altman>/None}",
            "update_my_altname_access": "{access_updated: ok/nok}"
        }
        
        signal_action_dict = {
            "forward": lambda altname, signal_data: forward_signal_to(altname, signal_data),
            "register": lambda websocket, email, candidate, altname, client_type, access: register_websocket_candidate(websocket, email, candidate, altname, client_type, access),
            "my_websocket_requested_altnames": lambda websocket: get_current_websocket_requested_altnames(websocket),
            "public_altname": lambda : get_public_altname_candidate()
        }
        
        await websocket.send_json(response)
		
	