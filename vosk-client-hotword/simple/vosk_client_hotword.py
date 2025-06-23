import argparse
import asyncio
import json
import logging
import os
import queue
import sounddevice as sd
import sys
import websockets
import time
from eff_word_net.audio_processing import Resnet50_Arc_loss
from eff_word_net.engine import HotwordDetector
from eff_word_net import samples_loc
from eff_word_net.streams import SimpleMicStream
from vosk import Model, KaldiRecognizer
import pathlib

q = queue.Queue()

global parse_once
global args
global loop
global audio_queue
parse_once = True

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
# Audio callback for real-time streaming
def audio_callback(indata, frames, time, status):
    if status:
        print("Error:", status)
    q.put(indata.copy())

# Transcribe with Vosk

def callback_vosk(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""

    global parse_once
    global args
    global loop
    global audio_queue
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

async def listen_and_transcribe(duration=5):

    global parse_once
    global args
    global loop
    global audio_queue
    global settings
    loop = asyncio.get_running_loop()
    if parse_once:
        parse_once = False
        parse_args()

    if int(settings.get('debug',0)) == 1 : 
        print("recording : ... ")
    with sd.RawInputStream(samplerate=settings.get("samplerate",16000),
                           blocksize = 4000, device=args.device, dtype='int16',
                           channels=1, callback=callback_vosk) as device:

        start = time.time()
        last_partial = time.time()
        had_any_text = False

        async with websockets.connect(settings.get("server", "ws://localhost:2700")) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (device.samplerate))
            while time.time() - start < duration or (had_any_text  and time.time() - last_partial < 5) :
                data = await audio_queue.get()
                await websocket.send(data)
                rec = await websocket.recv()
                parsed = json.loads(rec)

                if "partial" in parsed and parsed["partial"] != ""  and had_any_text:
                    last_partial = time.time()
                elif "text" in parsed and parsed["text"] != "":
                    had_any_text = True
                    last_partial = time.time()
                    print(parsed["text"])


            await websocket.send('{"eof" : 1}')
            #print(await websocket.recv())
    if int(settings.get('debug',0)) == 1 : 
        print("stopped recording")


def parse_args():

    global parse_once
    global args
    global loop
    global audio_queue
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(description="ASR Server",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[parser])
    parser.add_argument('-d', '--device', type=int_or_str,
                        help='input device (numeric ID or substring)')
    args = parser.parse_args(remaining)
    audio_queue = asyncio.Queue()
    logging.basicConfig(level=logging.INFO)

async def main():

    base_model = Resnet50_Arc_loss()

    global settings
    settings_file = pathlib.Path(__file__).parent / 'client_settings.json'
    settings = json.load(open(settings_file)) if settings_file.exists() else {
            "debug" : 0,
            "hotword_threshold" : 0.6,
            "relaxation_time" : 2,
            "hotword" : "mycroft",
            "hotword_refference_file" : "~/.local/lib/python3.9/site-packages/eff_word_net/sample_refs/mycroft_ref.json",
            "server" : "ws://localhost:2700",
            "sample_rate_to_server" : 16000,
    }



    if int(settings.get('debug',0)) == 1 : 
        print("Say",settings.get("hotword", "mycroft")) 

    mycroft_hw = HotwordDetector( 
                                 hotword=settings.get("hotword", "mycroft"), 
                                 model = base_model, 
                                 reference_file= os.path.expanduser(settings.get("hotword_refference_file", os.path.join(samples_loc, "mycroft_ref.json"))),
                                 threshold=float(settings.get("hotword_threshold", 0.6)),
                                 relaxation_time=int(settings.get("relaxation_time", 2)),
                                 )

    mic_stream = SimpleMicStream(
            window_length_secs = 1.5, # these are ratios for that depend on constants internally so no config othewise the buffers break since sizes are kinda hradcoded 
            sliding_window_secs=0.75
            )
    mic_stream.start_stream()

    while True :
        frame = mic_stream.getFrame()
        result = mycroft_hw.scoreFrame(frame)
        if result==None :
            #no voice activity
            continue
        if(result["match"]):
            if int(settings.get('debug',0)) == 1 : 
                print("Wakeword uttered",result["confidence"])
            await listen_and_transcribe()

if __name__ == '__main__':
   asyncio.run( main())

