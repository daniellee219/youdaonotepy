#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ynote
import webbrowser
import os.path
import ynote.oauth2 as oauth2

consumer_key = 'your consumer key'
consumer_secret = 'your consumer secret'

token_file = 'demo.token'

client = ynote.YNoteClient(consumer_key, consumer_secret)
if os.path.exists(token_file):
    f = open(token_file)
    client.access_token = oauth2.Token(f.readline().strip(), f.readline().strip())
    f.close()
else:
    auth_url = client.grant_request_token(None)
    print 'auth_url = '+auth_url
    webbrowser.open(auth_url)
    verifier = raw_input('Input verifier:')
    client.grant_access_token(verifier)
    print 'access_token=%s, secret=%s' % (client.access_token.key, client.access_token.secret)
    f = open(token_file, 'w')
    f.write(client.access_token.key+"\n"+client.access_token.secret)
    f.close()

print '\get user info\n---------------------------'
user = client.get_user()
print user.__dict__

print '\nget notebooks\n----------------------------'
books = client.get_notebooks()
print books

print '\nget notes in the default notebook\n-----------------------'
note_paths = client.get_note_paths(user.default_notebook)
print note_paths

print '\ncreate notebook\n------------------------'
bookpath = client.create_notebook('book1')
print 'new_book_path='+bookpath

print '\nget note\n----------------------'
note = client.get_note(note_paths[0])
print note.__dict__

print '\ncreate note\n---------------------'
new_note = ynote.Note()
new_note.source = u'lic'
new_note.author = u'lichuan'
new_note.title = u'我是谁？'
new_note.content = u'hehe哈哈哈'
new_note.path = client.create_note(user.default_notebook, new_note)
print "new_note_path="+new_note.path

#pdb.set_trace()
#print '\ncreate incomplete note\n---------------------'
#new_note = ynote.Note()
#new_note.source = None
#new_note.author = u'lichuan'
#new_note.title = u'我是谁？'
#new_note.content = u'hehe哈哈哈'
#new_note.path = client.create_note(user.default_notebook, new_note)
#print "new_note_path="+new_note.path

print '\nupdate note\n--------------------'
new_note.content += u" updated"
client.update_note(new_note)

print '\nmove note\n-------------------'
new_note.path = client.move_note(new_note.path, bookpath)
print 'new_path='+ new_note.path

print '\nshare note\n----------------------'
shared_url = client.share_note(new_note.path)
print 'shared_url='+shared_url

print '\nupload image\n-------------------'
res_file = open('demo_upload.jpg')
res = client.upload_resource(res_file)
res_file.close()
print res.to_resource_tag()

print '\nupdate note with image\n--------------------'
new_note.content += res.to_resource_tag()
client.update_note(new_note)

print '\ndownload image\n--------------------'
image_file = open('demo_download.jpg', 'w')
image_file.write(client.download_resource(res.url))
image_file.close()

print '\ndelete note\n---------------------'
client.delete_note(new_note.path)
new_book_notes = client.get_note_paths(bookpath)
print 'new_book_note_paths:',new_book_notes

print '\ndelete notebook\n-----------------'
client.delete_notebook(bookpath)
