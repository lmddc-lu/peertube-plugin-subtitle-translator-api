PHONY: build run

build:
	docker build -t subtitle_translator_api .

run: build
	docker run -p 5000:80 subtitle_translator_api