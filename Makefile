SHELL := $(shell which bash)
default: info
info:
	@echo $(SHELL)
	@echo "Usage:"
	@echo "  make install_python_only    # Install Python 3.9.23"
	@echo "  make install_vosk_only      # Install Vosk and its dependencies"
	@echo "  make install_eff_word_only  # Install EfficientWord-Net and its dependencies"
	@echo "  make install_python         # Install Python only"
	@echo "  make install_vosk           # Install Python and Vosk"
	@echo "  make install_eff_word       # Install Python and EfficientWord-Net"
	@echo "  make install_all            # Install everything (Python, Vosk, EfficientWord-Net)"
	@echo "  make setup_service          # Setup the Vosk server as systemd service"

install_python_only:
	# preequisites for Python
	sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev \
		libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev \
		libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

	[[ -e Python-3.9.23.tar.xz ]] || wget https://www.python.org/ftp/python/3.9.23/Python-3.9.23.tar.xz
	[[ -d Python-3.9.23 ]] || tar -xf Python-3.9.23.tar.xz

	cd Python-3.9.23 && \
	./configure --enable-optimizations && \
	make -j && sudo make altinstall

install_vosk_only:
	pip3.9 install vosk
	[[ -d ~/.local/share/vosk/models ]] || mkdir -p ~/.local/share/vosk/models
	[[ -e ~/.local/share/vosk/models/vosk-model-small-en-us-0.15.zip ]] || wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -P ~/.local/share/vosk/models/
	[[ -d ~/.local/share/vosk/models/vosk-model-small-en-us-0.15 ]] || unzip -o ~/.local/share/vosk/models/vosk-model-small-en-us-0.15.zip -d ~/.local/share/vosk/models/


install_eff_word_only:
	sudo apt -y install portaudio19-dev libalsaplayer0 libalsaplayer-dev
	pip3.9 install wheel
	pip3.9 install pyaudio
	pip3.9 install sounddevice
	pip3.9 install tflite tflite-runtime
	pip3.9 install EfficientWord-Net
	# Quick Fix for EfficientWord-Net error
	[[ -e ~/.local/lib/python3.9/site-packages/eff_word_net/streams.py ]] && sed -i 's/np.frombuffer(mic_stream.read(CHUNK),dtype=np.int16)/np.frombuffer(mic_stream.read(CHUNK, False),dtype=np.int16)/g' ~/.local/lib/python3.9/site-packages/eff_word_net/streams.py
	[[ -d ~/.local/share/eff_word_net ]] || mkdir -p ~/.local/share/eff_word_net # here we will store the modlels
	@echo "Pi might need a restart if running the client with hotword recognition fails"

install_python:   install_python_only
install_vosk:     install_python      install_vosk_only
install_eff_word: install_python      install_eff_word_only
install_all:      install_python_only install_vosk_only install_eff_word_only

install_zerotier:
	curl -s  https://install.zerotier.com  | sudo bash

setup_service:
	[[ -d ~/.local/share/vosk ]] || mkdir -p ~/.local/share/vosk
	cp vosk-server/server.py ~/.local/share/vosk
	cp vosk-server/server_settings.json ~/.local/share/vosk
	sudo cp vosk-server/vosk-ws.service /etc/systemd/system/vosk-ws.service
	sudo chmod 644 /etc/systemd/system/vosk-ws.service
	sudo systemctl start vosk-ws
	sudo systemctl enable vosk-ws.service
