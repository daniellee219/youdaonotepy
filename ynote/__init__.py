#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = "1.0b"
__author__ = "Li Chuan (daniellee0219@gmail.com)"

'''
Python client SDK for Youdao Note API using OAuth 2.
'''

try:
    import json
except ImportError:
    import simplejson as json

import urllib2, oauth2, time

ENCODING = 'utf-8'
BASE_URL = 'http://sandbox.note.youdao.com/'
OPTIONAL_BASE_URL = 'http://note.youdao.com/'

def _fix_url(url):
    if url.startswith(BASE_URL):
        return url
    else:
        return url.replace(OPTIONAL_BASE_URL, BASE_URL)


class User:
    """User class that represents a ynote user."""

    def __init__(self, json_dict=None):
        '''init with the data from a dictionary.'''
        if json_dict:
            self.id = json_dict['id']
            self.user_name = json_dict['user']
            self.total_size = json_dict['total_size']
            self.used_size = json_dict['used_size']
            self.register_time = int(json_dict['register_time'])
            self.last_login_time = int(json_dict['last_login_time'])
            self.last_modify_time = int(json_dict['last_modify_time'])
            self.default_notebook = json_dict['default_notebook']
        else:
            self.id = ""
            self.user_name = ""
            self.total_size = 0
            self.used_size = 0
            self.register_time = 0
            self.last_login_time = 0
            self.last_modify_time = 0
            self.default_notebook = ""


class Notebook:
    """Notebook class that represents a ynote notebook."""

    def __init__(self, json_dict=None):
        '''init with the data from a dictionary.'''
        if json_dict:
            self.path = json_dict['path']
            self.name = json_dict['name']
            self.notes_num = int(json_dict['notes_num'])
            self.create_time = int(json_dict['create_time'])
            self.modify_time = int(json_dict['modify_time'])
        else:
            self.path = ""
            self.name = ""
            self.notes_num = 0
            self.create_time = 0
            self.modify_time = 0
    

class Note:
    """Note class that represents a ynote note."""
    
    def __init__(self, json_dict=None):
        '''init with the data from a dictionary.'''
        if json_dict:
            self.path = json_dict['path']
            self.title = json_dict['title']
            self.author = json_dict['author']
            self.source = json_dict['source']
            self.size = int(json_dict['size'])
            self.create_time = int(json_dict['create_time'])
            self.modify_time = int(json_dict['modify_time'])
            self.content = json_dict['content']
        else:
            self.path = ""
            self.title = ""
            self.author = ""
            self.source = ""
            self.size = 0
            self.create_time = -1
            self.modify_time = -1
            self.content = ""
           

class Resource:
    """Resource class that represents a resource in a note."""

    def __init__(self, json_dict):
        '''init with the data from a dictionary.'''
        if json_dict:
            self.url = _fix_url(json_dict['url'])
            if json_dict.has_key('src'):
                self.icon = _fix_url(json_dict['src'])
            else:
                self.icon = ""
        else:
            self.url = ""
            self.icon = ""

    def to_resource_tag(self):
        '''convert to an html tag'''
        if self.icon:
            return "<img path=\"%s\" src=\"%s\" />" % (self.url,self.icon)
        else:
            return "<img src=\"%s\" />" % self.url
    

class YNoteError(StandardError):
    '''
    SDK error class that represents API error as well as http error
    '''

    def __init__(self, error_type, error_code, message):
        '''init with error code and message.'''
        self.error_msg = message
        self.error_code = int(error_code)
        self.error_type = error_type
        StandardError.__init__(self, message)
    
    def __str__(self):
        '''convert to a string.'''
        return "YNoteError: type=%s, code=%d, message=%s" % (self.error_type, self.error_code, self.error_msg)


def _parse_api_error(body):
    '''parse an YNote API error to YNoteError object'''
    json_obj = json.loads(body)
    return YNoteError('API_ERROR', int(json_obj['error']), json_obj['message'])

def _parse_http_error(e):
    '''parse an urllib2.HTTPError object to YNoteError object'''
    return YNoteError('HTTP_ERROR', e.code, e.reason)

def _parse_urlencoded(body):
    '''parse an urlencoded string to dictionary'''
    parts = body.split('&')
    return dict([tuple(part.split('=')) for part in parts])


def _do_http(request):
    '''initiate an http request.'''
    try:
        resp = urllib2.urlopen(request)
        return resp.read()
    except urllib2.HTTPError, e:
        if e.code == 500:
            raise _parse_api_error(e.read())
        else:
            raise _parse_http_error(e)

def _do_get(url, params, consumer, token):
    '''
    initiate an http GET request, return result as a string or raise error.
    '''
    req_builder = oauth2.RequestBuilder(oauth2.HTTP_GET, url, params)
    req = req_builder.build_signed_request(consumer, token)
    return _do_http(req)

def _do_post(url, params, consumer, token):
    '''
    initiate an http POST request with urlencoded content,
    return result as string or raise error.
    '''
    return _do_post_urlencoded(url, params, consumer, token)

def _do_post_urlencoded(url, params, consumer, token):
    '''
    initiate an http POST request with urlencoded content,
    return result as string or raise error.
    '''
    req_builder = oauth2.RequestBuilder(oauth2.HTTP_POST_URLENCODED, url, params)
    req = req_builder.build_signed_request(consumer, token)
    return _do_http(req)

def _do_post_multipart(url, params, consumer, token):
    '''
    initiate an http POST request with multipart content,
    return result as string or raise error.
    '''
    req_builder = oauth2.RequestBuilder(oauth2.HTTP_POST_MULTIPART, url, params)
    req = req_builder.build_signed_request(consumer, token)
    return _do_http(req)


class YNoteClient:
    """API client for Youdao Note."""

    def __init__(self, consumer_key, consumer_secret):
        '''init with consumer key and consumer secret.'''
        self.consumer = oauth2.Consumer(consumer_key, consumer_secret)
        self.access_token = None
        self.request_token = None

    def grant_request_token(self, callback_url):
        '''get request token(store in self.request_token), return authorization url.'''
        if callback_url:
            params = {'oauth_callback':callback_url}
        else:
            params = {'oauth_callback':'oob'}

        res = _do_get(BASE_URL+'oauth/request_token', params, self.consumer, None)
        res_dict = _parse_urlencoded(res)
        self.request_token = oauth2.Token(res_dict['oauth_token'], res_dict['oauth_token_secret'])

        auth_url = BASE_URL + 'oauth/authorize?oauth_token=' + self.request_token.key
        if callback_url:
            auth_url += '&oauth_callback=' + callback_url
    
        return auth_url

    def grant_access_token(self, verifier):
        '''get access token(store in self.access_token).'''
        params = {
            'oauth_token':self.request_token.key,
            'oauth_verifier':verifier
        }

        res = _do_get(BASE_URL+'oauth/access_token', params, self.consumer, self.request_token)
        res_dict = _parse_urlencoded(res)
        self.access_token = oauth2.Token(res_dict['oauth_token'], res_dict['oauth_token_secret'])
    
    def set_access_token(self, token_key, token_secret):
        '''set the access token'''
        self.access_token = oauth2.Token(token_key, token_secret)

    def get_access_token(self):
        '''get current access token as key,secret'''
        if self.access_token:
            return self.access_token.key, self.access_token.secret
        else:
            return "", ""

    def get_user(self):
        '''get user information, return as a User object.'''
        res = _do_get(BASE_URL+'yws/open/user/get.json', None, self.consumer, self.access_token)
        return User(json.loads(res))

    def get_notebooks(self):
        '''get all notebooks, return as a list of Notebook objects.'''
        res = _do_post(BASE_URL+'yws/open/notebook/all.json', None, self.consumer, self.access_token)
        return [Notebook(d) for d in json.loads(res)]

    def get_note_paths(self, book_path):
        '''get path of all notes in a notebook, return as a list of path strings.'''
        params = {'notebook':book_path}
        res = _do_post(BASE_URL+'yws/open/notebook/list.json', params, self.consumer, self.access_token)
        return json.loads(res)
    
    def create_notebook(self, name, create_time=None):
        '''create a notebook with specified name.'''
        params = {'name':name}
        if create_time:
            params['create_time'] = create_time

        res = _do_post(BASE_URL+'yws/open/notebook/create.json', params, self.consumer, self.access_token)
        return json.loads(res)['path']
    
    def delete_notebook(self, path):
        '''delete a notebook with specified path.'''
        params = {'notebook':path}
        res = _do_post(BASE_URL+'yws/open/notebook/delete.json', params, self.consumer, self.access_token)

    def get_note(self, path):
        '''get a note with specified path, return as a Note object.'''
        params = {'path':path}
        res = _do_post(BASE_URL+'yws/open/note/get.json', params, self.consumer, self.access_token)
        return Note(json.loads(res))
    
    def create_note(self, book_path, note):
        '''create a note in a notebook with information specified in "note".'''
        params = {
            'source':note.source,
            'author':note.author,
            'title':note.title,
            'content':note.content,
            'notebook':book_path
        }
        res = _do_post_multipart(BASE_URL+'yws/open/note/create.json', params, self.consumer, self.access_token)
        return json.loads(res)['path']

    def create_note_with_attributes(self, book_path, content, **kw):
        '''create a note with attributes given by parameters'''
        params = { 'notebook':book_path, 'content':content }
        
        if 'source' in kw.keys():
            params['source'] = kw['source']

        if 'author' in kw.keys():
            params['author'] = kw['author']

        if 'title' in kw.keys():
            params['title'] = kw['title']

        if 'create_time' in kw.keys():
            params['create_time'] = kw['create_time']
        
        res = _do_post_multipart(BASE_URL+'yws/open/note/create.json', params, self.consumer, self.access_token)
        return json.loads(res)['path']
    
    def update_note(self, note, modify_time=None):
        '''update the note with information in "note".'''
        params = {
            'path':note.path,
            'source':note.source,
            'author':note.author,
            'title':note.title,
            'content':note.content,
        }
        if modify_time:
            params['modify_time'] = modify_time
            
        _do_post_multipart(BASE_URL+'yws/open/note/update.json', params, self.consumer, self.access_token)

    def update_note_attributes(self, note_path, **kw):
        '''update the some attributes(given by kw) of the note.'''
        params = {'path':note_path}
        
        if 'source' in kw.keys():
            params['source'] = kw['source']

        if 'author' in kw.keys():
            params['author'] = kw['author']

        if 'title' in kw.keys():
            params['title'] = kw['title']

        if 'content' in kw.keys():
            params['content'] = kw['content']

        if 'modify_time' in kw.keys():
            params['modify_time'] = kw['modify_time']
        
        _do_post_multipart(BASE_URL+'yws/open/note/update.json', params, self.consumer, self.access_token)

    def move_note(self, note_path, book_path):
        '''move note to the notebook with path denoted by "book_path".'''
        params = {
            'path':note_path,
            'notebook':book_path
        }
        res = _do_post(BASE_URL+'yws/open/note/move.json', params, self.consumer, self.access_token)
        return json.loads(res)['path']
    
    def delete_note(self, note_path):
        '''delete a note with specified path.'''
        params = {'path':note_path}
        res = _do_post(BASE_URL+'yws/open/note/delete.json', params, self.consumer, self.access_token)
    
    def share_note(self, note_path):
        '''share a note with specified path, return shared url.'''
        params = {'path':note_path}
        res = _do_post(BASE_URL+'yws/open/share/publish.json', params, self.consumer, self.access_token)
        return _fix_url(json.loads(res)['url'])

    def upload_resource(self, res_file):
        '''upload a file as a resource.'''
        params = {'file':res_file}
        res = _do_post_multipart(BASE_URL+'yws/open/resource/upload.json', params, self.consumer, self.access_token)
        return Resource(json.loads(res))
    
    def download_resource(self, resource_url):
        '''download a resource file with specified url, return as a string.'''
        res = _do_get(resource_url, None, self.consumer, self.access_token)
        return res
