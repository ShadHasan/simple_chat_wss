FROM tinyorb/python3.12:fastapi_googleauth
COPY copiable_content/chat_app /opt/chat_app
WORKDIR /opt/chat_app
RUN cd /opt/chat_app/cer && \
 openssl req -x509 -newkey rsa:2048 -nodes -keyout main.key -out main.cer\
 -days 365 -config cert.conf -extensions v3_req
# ENTRYPOINT ["python3", "-m", "fastapi", "dev", "endpoint.py", "--host", "0.0.0.0"]
ENTRYPOINT ["python3", "endpoint.py"]