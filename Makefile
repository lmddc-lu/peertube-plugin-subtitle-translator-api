.PHONY: build-gpu build-cpu stop run-cpu run-gpu run

include .env

stop:
	-docker stop subtitle_translator_api_cpu 2> /dev/null 
	-docker stop subtitle_translator_api_gpu 2> /dev/null
	-docker rm subtitle_translator_api_cpu 2> /dev/null
	-docker rm subtitle_translator_api_gpu 2> /dev/null

# This requires poetry and python 3.9 installed
build-subtitle-translator:
	cd vendor/Subtitles-Translator && poetry install && poetry build

build-cpu:
	docker build -t subtitle_translator_api -f ./Dockerfile.cpu .

build-gpu:
	docker build -t subtitle_translator_api -f ./Dockerfile.gpu .

run-cpu: stop build-cpu
	docker run --name subtitle_translator_api_cpu -d -p $(API_PORT):80 -v data:/code/data subtitle_translator_api

run-gpu: stop build-gpu
	docker run --name subtitle_translator_api_gpu --gpus all -d -p $(API_PORT):80 -v data:/code/data subtitle_translator_api

run:
	if [ $(USE_GPU) = "true" ]; then \
		$(MAKE) run-gpu; \
	else \
		$(MAKE) run-cpu; \
	fi