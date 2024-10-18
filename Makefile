PHONY: build run stop

stop:
	-docker stop subtitle_translator_api

build:
	docker build -t subtitle_translator_api -f ./Dockerfile.cpu .

build-gpu:
	docker build -t subtitle_translator_api -f ./Dockerfile.gpu .

run: stop build
	docker run -d -p 5000:80 -v data:/code/data subtitle_translator_api

run-gpu: stop build-gpu
	docker run --gpus-all -d -p 5000:80 -v data:/code/data subtitle_translator_api