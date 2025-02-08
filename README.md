# InterVillage Project
Welcome! This is a rather stupid project of mine that attempts to create an IMPS
server that also communicates through Discord and Signal to allow IMPS clients
to talk on these platforms.

### Why?
Because why not. As one wise man once said, "not everything in life has to have
a purpose". The motive behind it was to use it on my Razr V3, though its polling
is almost unusable so it's questionable.

### How?
IMPS client <<<http/xml (IMPS)>>> InterVillage <<<rest/ws>>> dc, signal etc.

Both channels are two-way, there isn't much more to it.

## Installation procedure
This assumes you have at least Python 3.11 installed.

First, create a venv and install all packages:
```
python -m venv venv
pip install -r requirements.txt
```
Next, copy ```secret-example.py``` into ```secret.py``` and edit its contents
as you need.

If necessary, setup signal-cli and place the ```signal``` executable into the
project root folder.

Once you're done, simply run with:
```
python app.py
```
You might want to use a real WSGI server instead though, as doing this runs a
**DEBUG** server.

## Contributions & LICENSE
If you genuinely want to contribute, thank you! Feel free to submit a pull request.
This project is licensed under GPLv3.0. Details can be found in the LICENSE file.
Thanks for checking this random code I wrote out!

<sup>Sorry, I don't have time to make a more technical writeup right now.
If you know Python, the code *should* be fairly easy to understand.