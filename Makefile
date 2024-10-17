PHONY: build run stop

stop:
	-docker stop subtitle_translator_api

build:
	docker build -t subtitle_translator_api -f ./Dockerfile.cpu .

run: stop build
	docker run -d -p 5000:80 -v data:/code/data subtitle_translator_api

run-gpu: stop build
	docker run --gpus-all -d -p 5000:80 -v data:/code/data subtitle_translator_api