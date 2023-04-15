import unittest
from server import create_parser, response_msg, send_message, main

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

    def test_parser_port(self):
        parser = create_parser()
        parsed = parser.parse_args(['-p', '8888'])
        port = parsed.port
        self.assertEqual(port, '8888')
    
    def test_response_message_auth_200(self):
        self.assertEqual(response_msg({
            "action": "authenticate", 
            "user": {
                "account_name": "C0deMaver1ck",
                "password": "CorrectHorseBatterStaple"
            }}),({
                "response": 200,
                "alert":"Все ок"
                }))
        
    def test_response_message_auth_402(self):
        self.assertEqual(response_msg({
            "action": "authenticate", 
            "user": {
                "account_name": "C0deMaver1ck",
                "password": ""
            }}), ({
                "response": 402,
                "error": 'This could be "wrong password" or "no account with that name"'
                }))



if __name__ == "__main__":
    unittest.main()