﻿import json
import logging
import os
import sys
import adal

def turn_on_logging():
    handler = logging.StreamHandler()
    adal.set_logging_options({
        'level': adal.LOGGING_LEVEL.DEBUG,
        'handler': handler 
    })

# You can provide account information by using a JSON file. Either
# through a command line argument, 'python sample.js parameters.json', or
# specifying in an environment variable.
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
    
authority_url = (sample_parameters['authorityHostUrl'] + '/' + 
                 sample_parameters['tenant'])
resource = '00000002-0000-0000-c000-000000000000'

turn_on_logging()

context = adal.AuthenticationContext(authority_url)

token = context.acquire_token_with_client_credentials(
    resource,
    sample_parameters['clientId'], 
    sample_parameters['clientSecret'])
