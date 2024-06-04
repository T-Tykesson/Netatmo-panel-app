FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip
RUN python3 -m pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Create and set permissions for the cache directory
RUN mkdir /.cache
RUN chmod 777 /.cache

# CMD should be at the end
CMD panel serve /code/app.py \
    --address 0.0.0.0 \
    --port 8080 \
    --allow-websocket-origin "*" \
    --index app \
