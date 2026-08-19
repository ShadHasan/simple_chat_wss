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
            "<altname_1>",
            "<altname_3>"
        ]
    }
    """
	
    
    def __init__(self):
        pass
        # load email_altname from database

	def register_websocket_candidate(websocket, email, candidate, altname, client_type, access=private):
        pass
        
    def get_public_altname_candidate():
        pass
        
    def get_candidate_by_altname(altname):
        pass
        
    
    def forward_signal_to(altname, signal_data):
        pass
        
    def get_current_websocket_requested_altnames():
        pass
		
	