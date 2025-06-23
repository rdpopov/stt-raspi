# stt-raspi

## Setup
### Server
Look into the Makefile
Generally there are 2 main things to setup: either vosk or efficient-word-net
- for vosk:
```bash
make install_vosk
```

It is intended for the server to be ran a as a service, so you can use the
Makefile to start it: if setup this way it will be using your current user as
the service user, the models are always located in `~/.local/share/vosk/models/`
the server script will be at `~/.local/share/vosk/server.py` and the
`server_config.json` file will be at `~/.local/share/vosk/server_config.json`.

```bash
make setup_service # this will setup the systemd service
```
- Example config:
```json
{ "modelpath": "~/.local/share/vosk/models/vosk-model-small-en-us-0.15",
    "port": 2700,
    "sample_rate": 16000,
    "spkmodel": ""
}
```

### Client
- for efficient-word-net: 
```bash
make install_eff_word
```

Since this is intened to be used as a module of a larger applicaiton, setting it
up as a service directly is not recommended. Similar setup to the server, the
config file must be in the same directory as the server script.

```json
{
    "debug" : 0,
    "hotword_threshold" : 0.6,
    "relaxation_time" : 2,
    "hotword" : "mycroft",
    "hotword_refference_file" : "~/.local/lib/python3.9/site-packages/eff_word_net/sample_refs/mycroft_ref.json",
    "server" : "ws://localhost:2700",
    "sample_rate_to_server" : 16000
}
```
### Client with custom hotword
- Create a custom hotword reference file using the `eff_word_net` CLI tool:
``` bash
# record a 4-10 samples of your hotword
TODO:
```

- Then generate the reference file:
``` bash
	python3.9 -m eff_word_net.generate_reference
```

## Usage
### Server
Run the server script:
```bash
python3.9 ROOT/vosk-server/server.py
```
Running the cleint script:

```bash
python3.9 ROOT/vosk-client-hotword/simple/vosk_client_hotword.py
```
