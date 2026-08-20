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
        
    def signal_directive_switch(self, websocket, data):
        signal_response = {
            "candidate_register": ["ok", "nok"],
            "signal_forward": ["ok", "nok"],
            "fetch_candidate": ["ok", "nok"]
        }
        
        signal_action_dict = {
            "forward": lambda altname, signal_data: forward_signal_to(altname, signal_data),
            "register": lambda websocket, email, candidate, altname, client_type, access: register_websocket_candidate(websocket, email, candidate, altname, client_type, access),
            "my_websocket_requested_altnames": lambda websocket: get_current_websocket_requested_altnames(websocket),
            "public_altname": lambda : get_public_altname_candidate()
        }
        
        data["action"]
		
	