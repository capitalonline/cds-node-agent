FROM ubuntu:20.04

ENV SYSTEMD_IGNORE_CHROOT=yes
ADD requirements.txt .
RUN apt-get update && apt-get install -y python3 pip && pip3 install -r requirements.txt
ADD . /app
CMD ["python3", "/app/src/main.py"]