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

#
# You can override the default account information by providing a JSON file
# with the same parameters as the sampleParameters variable below.  Either
# through a command line argument, 'python sample.js parameters.json', or
# specifying in an environment variable.
# {
#    "tenant" : "rrandallaad1.onmicrosoft.com",
#    "authorityHostUrl" : "https://login.windows.net",
#    "clientId" : "",
#    "anothertenant" : "bar.onmicrosoft.com"
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
        "tenant" : 'convergeTest.onmicrosoft.com',
        "authorityHostUrl" : 'https://login.windows.net',
        "clientId" : '',
        "anothertenant" : ''
    }

authority_host_url = sample_parameters['authorityHostUrl']
authority_url = authority_host_url + '/' + sample_parameters['tenant']
clientid = sample_parameters['clientid']
resource = '00000002-0000-0000-c000-000000000000'

#no verbose, which obscures the device code message 
#turn_on_logging()

context = adal.AuthenticationContext(authority_url)
code = context.acquire_user_code(resource, clientid)
print(code['message'])
token = context.acquire_token_with_device_code(resource, code, clientid)

#try cross tenant token refreshing
another_tenant = sample_parameters.get('anothertenant')
if another_tenant:
    authority_url = authority_host_url + '/' + another_tenant
    #reuse existing cache which has the tokens acquired early on 
    existing_cache = context.cache
    context = adal.AuthenticationContext(authority_url, cache=existing_cache)
    token = context.acquire_token(resource, token['userId'], clientid)



