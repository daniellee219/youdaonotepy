# Youdao Note Python SDK

Python SDK for [Youdao Note](http://note.youdao.com/) which provides
* OAuth2.0 authentication
* API calling wrapper

Developed and maintained By [Daniel Lee](mailto:daniellee0219@gmail.com). All your bug reports and suggestions are welcome.

# How to change base URL

To prevent damages by unqualified applications, Youdao Note created an environment called the `Sandbox Environment`, which is completely isolated to the `Online Environment` so that you can test your application without modifying any existing data. You can switch to the `Sandbox Environment` by setting the `BASE_URL` as following:

```python
import ynote

ynote.BASE_URL = 'http://sandbox.note.youdao.com/'
```
or switch to the `Online Environment` by doing:
```python
ynote.BASE_URL = 'http://note.youdao.com/'
```
Note that the SDK uses the `Sandbox Environment` by default.

# How to get privileges to Youdao Note API

To access the Youdao Note API, you must setup your account at [Youdao Note API](http://note.youdao.com/open/) and apply for an API key. As soon as Youdao Note accepts your application, you'll receive your `Consumer Key` and `Consumer Secret`. Put these environment variables as constants in your code:

```python
CONSUMER_KEY = 'Your Consumer Key'
CONSUMER_SECRET = 'Your Consumer Secret'
```

Then create a client with them:

```python
client = ynote.YNoteClient(CONSUMER_KEY, CONSUMER_SECRET)
```

Before accessing the actual API, call the following functions in turn to grant the privileges:

```python
auth_url = client.grant_request_token(your_callback_url)
client.grant_access_token(verifier)
```
Note that:
* `your_callback_url` is the url that the user should be redirected to after authentication.
* `verifier` is the verification code that can be obtained by openning `auth_url`.

The access token, which can be reused to access the open API before it expires, will be stored in `client.access_token`. You can read and write by accessing this attribute directly or calling:

```python
token_key,token_secret = client.get_access_token()  # Read
client.set_access_token(token_key, token_secret)    # Write

```

# How to access Youdao Note API

After getting the privileges, you can call the following methods to access the Youdao Note API:
```python
user = client.get_user()
books = client.get_notebooks()
note_paths = client.get_note_paths(user.default_notebook)
bookpath = client.create_notebook('book1')
note = client.get_note(note_paths[0])
new_note.path = client.create_note(user.default_notebook, new_note)
client.update_note(new_note)
new_note.path = client.move_note(new_note.path, bookpath)
shared_url = client.share_note(new_note.path)
\# ......
```
For more methods and detailed usage of them, plese refre to [the wiki](https://github.com/daniellee219/youdaonotepy/wiki)
