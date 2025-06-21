# stt-raspi

## Setup
Look into the Makefile
Generally there are 2 main things to setup: either vosk or efficient-word-net
- for vosk:
```bash
make install_vosk
```

- for efficient-word-net: 
```bash
make install_eff_word
```
## Usage

it is intended for the server to be ran a as a service, so you can use the Makefile to start it:
```bash
make setup_service
```
