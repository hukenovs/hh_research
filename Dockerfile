# Dockerfile
# #############################################################################
#
# Build image:
# >> docker build -t hh-api .
#
# Run container:
# >> docker run --rm --name my-app -it -p 3333:3333 hh-api
#
# #############################################################################

FROM        python:3.8
LABEL       maintainer="Alexander Kapitanov"
LABEL       source="https://github.com/capitanov/hh_research"
WORKDIR     /workdir
COPY        . .

RUN         pip install --upgrade pip && pip install --no-cache-dir -r /workdir/requirements.txt

EXPOSE      3333
CMD         jupyter notebook --port 3333 --no-browser --ip 0.0.0.0 --allow-root
