FROM mongo:3.2.12 
MAINTAINER Feiqiao Wang "feiqiao.wang@stonybrook.edu" 

RUN apt-get -y update && \
    apt-get -y install python python-dev python-pip curl git wget && \
    curl -sL https://deb.nodesource.com/setup_7.x | bash - && \
    apt-get install -y nodejs

RUN npm install -g forever && \
    pip install --upgrade setuptools && \
    pip install cwlref-runner && \
    wget https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    chmod 0755 jq-linux64 && mv jq-linux64 /usr/local/bin/. 

RUN mkdir -p /root/quip_cwl
WORKDIR /root/quip_cwl

ADD . /root/quip_cwl/
RUN npm install
 
ENV PATH=$PATH:"/root/quip_cwl/bin"
ENV PATH=$PATH:"./"

# change file to executable mod
RUN cd bin && \
    chmod 777 runSegmentCuration.sh

CMD ["node","worker_cwl.js"]
