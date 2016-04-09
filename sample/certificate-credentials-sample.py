import json
import logging
import sys
import adal

def turn_on_logging():
    handler = logging.StreamHandler()
    adal.set_logging_options({
        'level': adal.LOGGING_LEVEL.DEBUG,
        'handler': handler 
    })

def get_private_key(filename):
    with open(filename, 'r') as pem_file:
        private_pem = pem_file.read()
    return private_pem

#
# You can override the default account information by providing a JSON file
# with the same parameters as the sampleParameters variable below.  Either
# through a command line argument, 'python sample.js parameters.json', or
# specifying in an environment variable.
# privateKeyFile must contain a PEM encoded cert with private key.
# thumbprint must be the thumbprint of the privateKeyFile.
# {
#   tenant : 'naturalcauses.onmicrosoft.com',
#   authorityHostUrl : 'https://login.windows.net',
#   clientId : 'd6835713-b745-48d1-bb62-7a8248477d35',
#   thumbprint : 'C1:5D:EA:86:56:AD:DF:67:BE:80:31:D8:5E:BD:DC:5A:D6:C4:36:E1',
#   privateKeyFile : 'ncwebCTKey.pem'
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
      'tenant' : 'naturalcauses.com',
      'authorityHostUrl' : 'https://login.windows.net', #TODO: replace with newer one
      'clientId' : 'd6835713-b745-48d1-bb62-7a8248477d35',
      'thumbprint' : 'C15DEA8656ADDF67BE8031D85EBDDC5AD6C436E1',
      'privateKeyFile' : ''
    }

authority_url = (sample_parameters['authorityHostUrl'] + '/' + 
                 sample_parameters['tenant'])
resource = '00000002-0000-0000-c000-000000000000'

turn_on_logging()

context = adal.AuthenticationContext(authority_url);
key = get_private_key(sample_parameters['privateKeyFile']);

token = context.acquire_token_with_client_certificate(
    resource, 
    sample_parameters['clientId'], 
    key, 
    sample_parameters['thumbprint'])
