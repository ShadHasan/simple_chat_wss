class SignalManager:

	candidate_socket_map = {}
    """
	{
		<ws>: {
			"access": "public/private",
			"candidate": <candidate>,
			"altname": ""
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
        # load email_altname

	def register_websocket_candidate(websocket, email, candidate, altname):
        pass
        
    def get_public_altname_candidate():
        pass
		
		
	