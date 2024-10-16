FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt update && apt install -y python3 python3-pip

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt


RUN pip install --upgrade -r /code/requirements.txt

COPY ./app /code/app


CMD ["fastapi", "run", "app/main.py", "--port", "80", "--workers", "8"]