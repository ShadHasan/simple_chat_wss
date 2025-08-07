FROM tinyorb/wss_chat:2.0
RUN rm -rf /opt/chat_app || true
COPY src /opt/chat_app
WORKDIR /opt/chat_app