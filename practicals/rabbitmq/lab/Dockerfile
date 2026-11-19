FROM python:3.13-slim
RUN pip install --no-cache-dir pika==1.3.2
WORKDIR /w
COPY rmq.py /usr/local/bin/rmq
RUN chmod +x /usr/local/bin/rmq
ENTRYPOINT ["rmq"]
