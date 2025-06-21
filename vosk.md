# Vosk setup
## Hardware: 
- Raspberry Pi 5 with 4GB RAM - apparently pi3 and pi4 models also work it is
  possible for maybe the pi zero 2 to be able to run it, but not sure. But maybe
  only something simple on top. (only the lightest models of the pi zero )

## Server setup
### Vosk server install
- install python from source
```bash
wget https://www.python.org/ftp/python/3.9.23/Python-3.9.23.tar.xz
tar -xf Python-3.9.23.tar.xz
```

- prerequisites
```bash
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev \
libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev \
libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
```

- in directory Python-3.9.23
```bash
./configure --enable-optimizations
make -j 4
sudo make altinstall
```
### Setup vosk server
- Install vosk
``` bash
python3.9 -m pip install vosk
```

- Download vosk test stuff to verify
```bash
git clone https://github.com/alphacep/vosk-api
cd vosk-api/python/example
python3.9 ./test_simple.py test.wav
# result should be something like:
#
# "text" : "zero one eight zero three"
```
- Apparently there are nodejs bindings for vosk via ffi.

### Setup vosk for on device processing (no hotword deection)

- Install sounddevice
```bash
sudo apt install portaudio19-dev # needed for sounddevice
python3.9 -m pip install sounddevice
```
- Run just the server as a slave(rp pi 5 fan doesn't spin up even when running
  the server)
``` bash
vosk-api/python/example
python3.9 test_microphone.py
```
This is for test purposes, almost always we will want to have the surver a s a
deamon, and connect to it via websockets. Also set up as a systemd service(or
whatever init system is in use).

### Setup vosk websocket sever on port (simple)
Vosk server examples 
For this server setup we are going to use websockets.
``` bash 
git clone https://github.com/alphacep/vosk-server
cd vosk-server/websocket
```
We are also going to need models for this, so we get them from [Vosk
models](https://alphacephei.com/vosk/models).
Small models are preferred for the pi as we are ram limited.
according to the [vosk documentation](https://alphacephei.com/vosk/models) the
larger models need more ram. So maybe a second hand thinkpad (or similar) with
16GB could be a good option for a server. I will expand on the server setup
later with some solutions.

``` bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vsk-small
# documentatation suggest /opt dir for this
```
- While setting it up so we have a client server is a little overkill, it is
  good for managment and simplicity.

- Also we can have hotword/wakeword detection with the client server setup.
``` bash
# example of running the server
# in 'vosk-server/websocket dir

python3.9 asr_server.py ~/vosk/vosk-models/vsk-small/
# NOTE:
# there may be an error in the original repo, one of the functions has one extra
# argument that has no use, so the `recognize` function should be changed to only
# have one argument.
```

## Client

### Client (simple setup)
``` bash
# running the client: 
# also in 'vosk-server/websocket dir'
# NOTE: static adressing is recommended
./test_microphone.py -u ws://192.168.0.103:2700
# here python version is not important since we are just piping microphone to the server
```


### Client with hotword detection
There isnt really an ideal wake wort detection solution. It either

- requires api keys(most likely paid) [picovoice](https://picovoice.ai/).
- or is not supported anymore [snowboy](https://snowboy.kitt.ai/). At least
  officialy, but there is a [fork](https://github.com/seasalt-ai/snowboy) that
  also has a way to generate custom hotwords. And while it is abandoned, it
  still works.

- [EfficientWord-Net](https://github.com/Ant-Brain/EfficientWord-Net) is a newer
  solution, still comperable or better performance to snowboy, but not
  depricated at least. as for features from what i can tell its trying to get to
  approach picovoice. It is however FOSS. It would also require python3.9 at
  most, so previous setup apllies.

#### EfficientWord-Net setup
  - Install EfficientWord-Net
```bash
  sudo apt install portaudio19-dev # needed for pyaudio
  pip3.9 install wheel
  pip3.9 install pyaudio
  pip3.9 install tflite tflite-runtime
  pip3.9 install EfficientWord-Net
```
- Currently might require a modification to the source code, that causes it to
  error otherwise. The issue is from last year, but has not been adressed yet.
  However I will describe the change here.

  In file 'site-packages/eff_word_net/streams.py' which with the current
  instructuions is located at 
  `~/.local/lib/python3.9/site-packages/eff_word_net/streams.py`.
  This line:
  ``` python3
       np.frombuffer(mic_stream.read(CHUNK),dtype=np.int16) 
  ```
  should be changed to:
  ``` python3
       np.frombuffer(mic_stream.read(CHUNK, False),dtype=np.int16)
  ```
  According to this github [issue](https://github.com/Ant-Brain/EfficientWord-Net/issues/57)

- Run client



## Additional configuration

### Server setup as systemd service(optional but recommended)

Under linux runs as a systemd service, so it is easy to set up.
- create '/etc/systemd/system/vosk-ws.service'

```service
[Unit]
Description=Vosk Websocket Server
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=rosko
ExecStart=/usr/bin/env python3.9 /home/rosko/vosk/vosk-server/websocket/asr_server.py /home/rosko/vosk/vosk-models/vsk-small/

[Install]
WantedBy=multi-user.target

```
- Enable and start the service
```bash
sudo systemctl start vosk-ws
sudo systemctl enable vosk-ws.service
```

### Zerotier setup
Zerotier is a good option for a vpn, and it is free for personal use. Its cross
platform. Has a web interface to manage connections and ips. So some static
adressing is possible. In the past I have done remote desktop and game servers
over zerotier.

- Install zerotier
```bash 
 curl -s  https://install.zerotier.com  | sudo bash
```
- Join network
```bash
sudo zerotier-cli join network-id
```
network-id can be found in the zerotier web interface.


