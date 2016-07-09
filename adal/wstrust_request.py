#------------------------------------------------------------------------------
#
# Copyright (c) Microsoft Corporation. 
# All rights reserved.
# 
# This code is licensed under the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#------------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta

import requests

from . import log
from . import util
from . import wstrust_response
from .adal_error import AdalError 

_USERNAME_PLACEHOLDER = '{UsernamePlaceHolder}'
_PASSWORD_PLACEHOLDER = '{PasswordPlaceHolder}' 

class WSTrustRequest(object):

    def __init__(self, call_context, watrust_endpoint_url, applies_to):
        self._log = log.Logger('WSTrustRequest', call_context['log_context'])
        self._call_context = call_context
        self._wstrust_endpoint_url = watrust_endpoint_url
        self._applies_to = applies_to
        
    @staticmethod
    def _build_security_header():

        time_now = datetime.utcnow()
        expire_time = time_now + timedelta(minutes=10)

        time_now_str = time_now.isoformat()[:-3] + 'Z'
        expire_time_str = expire_time.isoformat()[:-3] + 'Z'

        security_header_xml = ("<wsse:Security s:mustUnderstand='1' xmlns:wsse='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'>"
                               "<wsu:Timestamp wsu:Id=\'_0\'>"
                               "<wsu:Created>" + time_now_str + "</wsu:Created>"
                               "<wsu:Expires>" + expire_time_str  + "</wsu:Expires>"
                               "</wsu:Timestamp>"
                               "<wsse:UsernameToken wsu:Id='ADALUsernameToken'>"
                               "<wsse:Username>" + _USERNAME_PLACEHOLDER + "</wsse:Username>"
                               "<wsse:Password>" + _PASSWORD_PLACEHOLDER + "</wsse:Password>"
                               "</wsse:UsernameToken>"
                               "</wsse:Security>")

        return security_header_xml

    @staticmethod
    def _populate_rst_username_password(template, username, password):
        password = WSTrustRequest._escape_password(password)
        return template.replace(_USERNAME_PLACEHOLDER, username).replace(_PASSWORD_PLACEHOLDER, password)

    @staticmethod
    def _escape_password(password):
        return password.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')

    def _build_rst(self, username, password):

        message_id = str(uuid.uuid4())
        rst_template = "<s:Envelope xmlns:s=\'http://www.w3.org/2003/05/soap-envelope\' xmlns:wsa=\'http://www.w3.org/2005/08/addressing\' xmlns:wsu=\'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd\'>\
          <s:Header>\
            <wsa:Action s:mustUnderstand=\'1\'>http://docs.oasis-open.org/ws-sx/ws-trust/200512/RST/Issue</wsa:Action>\
            <wsa:messageID>urn:uuid:{}</wsa:messageID>\
            <wsa:ReplyTo>\
              <wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address>\
            </wsa:ReplyTo>\
            <wsa:To s:mustUnderstand=\'1\'>{}</wsa:To>\
            {}\
          </s:Header>\
          <s:Body>\
            <wst:RequestSecurityToken xmlns:wst=\'http://docs.oasis-open.org/ws-sx/ws-trust/200512\'>\
              <wsp:AppliesTo xmlns:wsp=\'http://schemas.xmlsoap.org/ws/2004/09/policy\'>\
                <wsa:EndpointReference>\
                  <wsa:Address>{}</wsa:Address>\
                </wsa:EndpointReference>\
              </wsp:AppliesTo>\
              <wst:KeyType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Bearer</wst:KeyType>\
              <wst:RequestType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Issue</wst:RequestType>\
            </wst:RequestSecurityToken>\
          </s:Body>\
        </s:Envelope>".format(message_id, self._wstrust_endpoint_url, WSTrustRequest._build_security_header(), self._applies_to)

        self._log.debug('Created RST: \n' + rst_template)
        return WSTrustRequest._populate_rst_username_password(rst_template, username, password)

    def _handle_rstr(self, body):
        wstrust_resp = wstrust_response.WSTrustResponse(self._call_context, body)
        wstrust_resp.parse()
        return wstrust_resp

    def acquire_token(self, username, password):

        rst = self._build_rst(username, password)
        headers = {'headers': {'Content-type':'application/soap+xml; charset=utf-8',
                               'SOAPAction': 'http://docs.oasis-open.org/ws-sx/ws-trust/200512/RST/Issue'},
                   'body': rst}
        options = util.create_request_options(self, headers)
        self._log.debug("Sending RST to: %s", self._wstrust_endpoint_url)

        operation = "WS-Trust RST"
        resp = requests.post(self._wstrust_endpoint_url, headers=options['headers'], data=rst, allow_redirects=True)

        util.log_return_correlation_id(self._log, operation, resp)

        if not util.is_http_success(resp.status_code):
            return_error_string = "{} request returned http error: {}".format(operation, resp.status_code)
            error_response = ""
            if resp.text:
                return_error_string += " and server response: {}".format(resp.text)
                try:
                    error_response = resp.json()
                except ValueError:
                    pass

            raise AdalError(return_error_string, error_response)
        else:
            return self._handle_rstr(resp.text)
