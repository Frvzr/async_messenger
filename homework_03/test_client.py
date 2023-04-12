import unittest
from client import create_parser, response_msg, send_message, main
from socket import *
from datetime import datetime
class TestServer(unittest.TestCase):

    def test_parser_default_port(self):
        parser = create_parser()
        parsed = parser.parse_args()
        port = parsed.port
        self.assertEqual(port, 7777)
    
    def test_parser_default_addr(self):
        parser = create_parser()
        parsed = parser.parse_args()
        addr = parsed.addr
        self.assertEqual(addr, '')
    
    def test_parser_addr(self):
        parser = create_parser()
        parsed = parser.parse_args([ '-a', 'localhost'])
        addr = parsed.addr
        self.assertEqual(addr, 'localhost')
    
    def test_response_message_200(self):
        self.assertEqual(response_msg({
                "response": 200,
                "alert":"Все ок"
                }),({
                "action": "join",
                "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                "room": "#room_name"
                }))
        
    def test_response_message_probe(self):
        self.assertEqual(response_msg({
            "action": "probe",
            "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            }), ({
                    "action": "presence",
                    "time": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                    "type": "status",
                    "user": {
                    "account_name": "C0deMaver1ck",
                    "status": "Yep, I am here!"
                    }
                    }))



if __name__ == "__main__":
    unittest.main()