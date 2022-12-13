# Only used for experimental PoC ./confexport.py

FROM pandoc/core

WORKDIR /confexport

COPY requirements.txt /confexport

RUN apk add python3 py3-pip

RUN python3 -m pip install -r requirements.txt

