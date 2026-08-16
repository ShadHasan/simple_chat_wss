FROM tinyorb/python3:base
RUN apt update -y
RUN apt install libssl-dev -y
COPY copiable_content/requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt
RUN apt install -y iperf3 iproute2 inetutils-ping curl
RUN python3 -m pip install "fastapi[standard]"
COPY copiable_content/chat_app /opt/chat_app
WORKDIR /opt/chat_app
RUN mkdir -p /opt/chat_app/cer
RUN cd /opt/chat_app/cer && \
 openssl req -x509 -newkey rsa:2048 -nodes -keyout main.key -out main.cer\
 -days 365 -config cert.conf -extensions v3_req
# ENTRYPOINT ["python3", "-m", "fastapi", "dev", "endpoint.py", "--host", "0.0.0.0"]
ENTRYPOINT ["python3", "endpoint.py"]