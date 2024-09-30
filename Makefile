PHONY: build run stop

stop:
	-docker stop subtitle_translator_api

build:
	docker build -t subtitle_translator_api .

run: stop build
	docker run -p 5000:80 subtitle_translator_api