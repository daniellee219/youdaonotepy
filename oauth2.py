#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "1.0"
__author__ = "Li Chuan (daniellee0219@gmail.com)"

'''
OAuth2 module for Youdao Note client SDK.
'''

import binascii
import time
import random
import urllib
import urllib2
import hmac
import collections


def _escape(s):
    """Special replacement."""
    return urllib.quote(s, safe='~')

def _generate_timestamp():
    """Get seconds since epoch (UTC)."""
    return int(time.time()) 

def _generate_nonce(length=15):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])

def _encode_urlencoded(params):
    '''build urlencoded body.'''
    args = []
    for k, v in params.iteritems():
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            args.append('%s=%s' % (k, _escape(qv)))
        elif isinstance(v, collections.Iterable):
            for i in v:
                qv = i.encode('utf-8') if isinstance(i, unicode) else str(i)
                args.append('%s=%s' % (k, _escape(qv)))
        else:
            qv = str(v)
            args.append('%s=%s' % (k, _escape(qv)))
        
    return '&'.join(args)

def _encode_multipart(params):
    '''build a multipart/-data body with randomly generated boundary.'''
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    for k, v in params.iteritems():
        data.append('--%s' % boundary)
        if hasattr(v, 'read'):
            # file-like object:
            filename = getattr(v, 'name', '')
            data.append('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (k, filename))
            data.append(v.read() if v else "")
        else:
            data.append('Content-Disposition: form-data; name="%s"\r\n' % k)
            if v:
                data.append(v.encode('utf-8') if isinstance(v, unicode) else v)
            else:
                data.append("")
    data.append('--%s--\r\n' % boundary)
    return '\r\n'.join(data), boundary


class Consumer:
    '''Consumer with key and secret'''
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    
class Token:
    '''Token with key and secret'''
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


#Request types
HTTP_GET = 0
HTTP_POST_URLENCODED = 1
HTTP_POST_MULTIPART = 2

def _get_method(request_type):
    '''get method name for request type.'''
    try:
        return ['GET', 'POST', 'POST'][request_type]
    except:
        return ''

class RequestBuilder(dict):
    '''OAuth request builder'''

    def __init__(self, request_type, url, extra_params=None):
        '''init request builder'''
        self.request_type = request_type
        self.url = url

        if extra_params is not None:
            self.update(extra_params)

    def _sign(self, consumer, token):
        '''fill request with OAuth fields including signature.'''
        self['oauth_consumer_key'] = consumer.key

        if token:
            self['oauth_token'] = token.key

        self['oauth_timestamp'] = _generate_timestamp()
        self['oauth_nonce'] = _generate_nonce()
        self['oauth_version'] = '1.0'
        self['oauth_signature_method'] = SignatureMethod_HMAC_SHA1.name

        signature = SignatureMethod_HMAC_SHA1.sign(self, consumer, token)
        self['oauth_signature'] = signature

    def get_normalized_parameters(self):
        '''
        build a string that contains the parameters that must be signed.            
        '''
        if self.request_type == HTTP_POST_URLENCODED:
            items = [(k, v) for k, v in self.items() if k != 'oauth_signature']
        else:
            items = [(k, v) for k, v in self.items() if k.startswith('oauth_') and k != 'oauth_signature'] 

        encoded_str = urllib.urlencode(sorted(items), True)
        return encoded_str.replace('+', '%20')

    def _get_auth_header(self):
        '''Get the header(as dict) named "Authorization"'''
        oauth_params = ((k, v) for k, v in self.items()
                    if k.startswith('oauth_'))    
        stringy_params = ((k, _escape(str(v))) for k, v in oauth_params)
        header_params = ('%s="%s"' % (k, v) for k, v in stringy_params)
        params_header = ', '.join(header_params)

        auth_header = 'OAuth'
        if params_header:
            auth_header = "%s %s" % (auth_header, params_header)

        return auth_header

    def _get_urlencoded_body(self):
        '''get body for urlencoded post requests'''
        body_params = dict([(k, v) for k, v in self.items()
                    if not k.startswith('oauth_')])
        if not body_params:
            return ''

        return _encode_urlencoded(body_params)

    def _get_multipart_body_boundary(self):
        '''get body,boundary for multipart post requests'''
        body_params = dict([(k,v) for k,v in self.items() 
                    if not k.startswith('oauth_')])
        if not body_params:
            return ''

        return _encode_multipart(body_params)

    def build_signed_request(self, consumer, token):
        '''
        build a request signed by consumer and token, return request as instance of urllib2.Request.
        '''
        self._sign(consumer, token)
        
        if self.request_type == HTTP_GET:
            req = urllib2.Request(self.url, None)
        elif self.request_type == HTTP_POST_URLENCODED:
            body = self._get_urlencoded_body()
            req = urllib2.Request(self.url, body)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            body, boundary = self._get_multipart_body_boundary()
            req = urllib2.Request(self.url, body)
            req.add_header('Content-Type', 'multipart/form-data; boundary=%s; charset=UTF-8' % boundary)
        
        req.add_header('Authorization', self._get_auth_header())
        return req


class SignatureMethod_HMAC_SHA1:
    name = 'HMAC-SHA1'
    
    @classmethod
    def _signing_base(cls, request, consumer, token):
        '''build key and base string for request builder.'''
        sig = (
            _escape(_get_method(request.request_type)),
            _escape(request.url),
            _escape(request.get_normalized_parameters()),
        )

        key = '%s&' % _escape(consumer.secret)
        if token:
            key += _escape(token.secret)
        base_string = '&'.join(sig)
        
        return key, base_string

    @classmethod
    def sign(cls, request, consumer, token):
        """calculate the signature for the request builder."""
        key, base_string = cls._signing_base(request, consumer, token)

        # HMAC object.
        try:
            import hashlib # 2.5
            hashed = hmac.new(key, base_string, hashlib.sha1)
        except ImportError:
            import sha # Deprecated
            hashed = hmac.new(key, base_string, sha)

        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]
