import http.server
import json
import os
import random
import socketserver
import string
import sys
from urllib.parse import urlparse, parse_qs

from adal import AuthenticationContext
import logging

# You can provide account information by using a JSON file. Either
# through a command line argument, 'python sample.js parameters.json', or
# specifying in an environment variable
# {
#    "tenant" : "rrandallaad1.onmicrosoft.com",
#    "authorityHostUrl" : "https://login.microsoftonline.com",
#    "clientId" : "624ac9bd-4c1c-4687-aec8-b56a8991cfb3",
#    "clientSecret" : "verySecret=""
# }

parameters_file = (sys.argv[1] if len(sys.argv) == 2 else 
                   os.environ.get('ADAL_SAMPLE_PARAMETERS_FILE'))

if parameters_file:
    with open(parameters_file, 'r') as f:
        parameters = f.read()
    sample_parameters = json.loads(parameters)
else:
    raise ValueError('Please provide parameter file with account information.')

PORT = 8088
server_url = 'http://localhost:{}'.format(PORT)
TEMPLATE_AUTHZ_URL = ('https://login.windows.net/{}/oauth2/authorize?'+ 
                      'response_type=code&client_id={}&redirect_uri={}&'+
                      'state={}&resource={}')
resource = '00000002-0000-0000-c000-000000000000' #aad graph
redirect_uri = 'http://localhost:{}/getAToken'.format(PORT)
authority_url = (sample_parameters['authorityHostUrl'] + '/' + 
                 sample_parameters['tenant'])

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._redirect(server_url + '/login')
        elif self.path == '/login':
            auth_state = (''.join(random.SystemRandom() 
                          .choice(string.ascii_uppercase + string.digits)
                          for _ in range(48)))
            c = http.cookies.SimpleCookie()
            c['auth_state'] = auth_state
            authorization_url = TEMPLATE_AUTHZ_URL.format(
                sample_parameters['tenant'], 
                sample_parameters['clientId'], 
                redirect_uri, 
                auth_state, 
                resource)
            #self.send_header('Set-Cookie', c.output(header=''))
            #self.end_headers()
            self._redirect(authorization_url)
        elif self.path.startswith('/getAToken'):
            message = None
            is_ok = True
            try:
                token_response = self._acquire_token()
                message = 'response: ' + json.dumps(token_response)
                #Later, if the access token is expired it can be refreshed.
                auth_context = AuthenticationContext(authority_url)
                token_response = auth_context.acquire_token_with_refresh_token(
                    token_response['refreshToken'],
                    sample_parameters['clientId'],
                    sample_parameters['clientSecret'],
                    resource)
                message = (message + '\nrefreshResponse:' + 
                           json.dumps(token_response))
            except ValueError as exp:
                message = str(exp)
                is_ok = False
            self._send_response(message, is_ok)
    
    def _acquire_token(self):
        parsed = urlparse(self.path)
        code = parse_qs(parsed.query)['code'][0]
        state = parse_qs(parsed.query)['state'][0]
        c = cookie.SimpleCookie(self.headers["Cookie"])
        if state != c['auth_state']:
            raise ValueError('state does not match')
        auth_context = AuthenticationContext(authority_url)
        token = auth_context.acquire_token_with_authorization_code(
            code, 
            redirect_uri, 
            resource, 
            sample_parameters['clientId'], 
            sample_parameters['clientSecret'])
        return token

    def _redirect(self, url):
        self.send_response(307)
        self.send_header('Location',url)
        self.end_headers()

    def _create_authorization_url(self):
        TEMPLATE_AUTHZ_URL.format()

    def _send_response(self, message, is_ok=True):
        if is_ok:
            self.send_response(200, message)
        else:
            self.send_error(400, message)

httpd = socketserver.TCPServer(("", PORT), MyRequestHandler)

print("serving at port", PORT)
httpd.serve_forever()

