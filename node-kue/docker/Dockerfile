FROM mongo:3.2.12 
MAINTAINER Feiqiao Wang "feiqiao.wang@stonybrook.edu" 

RUN apt-get -y update && \
    apt-get -y install python python-dev python-pip curl git wget && \
    curl -sL https://deb.nodesource.com/setup_7.x | bash - && \
    apt-get install -y nodejs

RUN npm install -g forever && \
    pip install cwlref-runner && \
    wget https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    chmod 0755 jq-linux64 && mv jq-linux64 /usr/local/bin/. 

WORKDIR /root

RUN git clone -b quip_composite https://github.com/SBU-BMI/quip_cwl.git && \
    cd quip_cwl && \
    npm install
    
 
ENV PATH=$PATH:"/root/quip_cwl/bin"
ENV PATH=$PATH:"./"

WORKDIR /root/quip_cwl

# change file to executable mod
RUN cd bin && \
    chmod 777 runSegmentCuration.sh

CMD ["node","worker_cwl.js"]
