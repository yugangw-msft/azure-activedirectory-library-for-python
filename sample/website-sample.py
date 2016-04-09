import http.server
import json
import socketserver
import sys
from urllib.parse import urlparse, parse_qs

from adal import AuthenticationContext
import logging

#
# You can override the default account information by providing a JSON file
# with the same parameters as the sampleParameters variable below.  Either
# through a command line argument, 'python sample.js parameters.json', or
# specifying in an environment variable.
# {
#    "tenant" : "rrandallaad1.onmicrosoft.com",
#    "authorityHostUrl" : "https://login.windows.net",
#    "clientId" : "624ac9bd-4c1c-4687-aec8-b56a8991cfb3",
#    "clientSecret" : "verySecret=""
# }

parameters_file = (sys.argv[1] if len(sys.argv)==2 else 
                   os.environ.get('ADAL_SAMPLE_PARAMETERS_FILE'))

if parameters_file:
    with open(parameters_file, 'r') as f:
        parameters = f.read()
    sample_parameters = json.loads(parameters)
else:
    print('File {} not found, falling back to defaults: '.format(parameters_file));
    sample_parameters = {
        'tenant' : 'rrandallaad1.onmicrosoft.com',
        'authorityHostUrl' : 'https://login.windows.net',
        'clientId' : '624ac9bd-4c1c-4686-aec8-b56a8991cfb3',
        "clientSecret" : "verySecret="
    }

PORT = 8088
server_url = 'http://localhost:{}'.format(PORT)
TEMPLATE_AUTHZ_URL = ('https://login.windows.net/{}/oauth2/authorize?'+ 
                      'response_type=code&client_id={}&redirect_uri={}&'+
                      'state={}&resource={}')
resource = 'https://graph.windows.net/'#'https://management.core.windows.net'
redirect_uri = 'http://localhost:{}/getAToken'.format(PORT)
authority_url = (sample_parameters['authorityHostUrl'] + '/' + 
                 sample_parameters['tenant'])

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._redirect(server_url + '/login')
        elif self.path == '/login':
            self.state = 'mystate'
            #todo get secret
            self._redirect(server_url + '/auth')
        elif self.path == '/auth':
            authorization_url = TEMPLATE_AUTHZ_URL.format(
                sample_parameters['tenant'], 
                sample_parameters['clientId'], 
                redirect_uri, 
                'mystate', 
                resource)
            self._redirect(authorization_url)

        elif self.path.startswith('/getAToken'):
            token = self._acquire_token()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            content = ("<html><head><title>congratulations</title></head>"+
                       "<body><p>you have got the token</p></body></html>")
            self.wfile.write(content.encode())
    
    def _acquire_token(self):
        parsed = urlparse(self.path)
        code = parse_qs(parsed.query)['code'][0]
        auth_context = AuthenticationContext(authority_url)
        token = auth_context.acquire_token_with_authorization_code(
            code, 
            redirect_uri, 
            resource, 
            sample_parameters['clientId'], 
            sample_parameters['clientSecret'])
        return token

    def _redirect(self, url):
        self.send_response(301)
        self.send_header('Location',url)
        self.end_headers()

    def _create_authorization_url(self):
        TEMPLATE_AUTHZ_URL.format()

httpd = socketserver.TCPServer(("", PORT), MyRequestHandler)

print("serving at port", PORT)
httpd.serve_forever()

