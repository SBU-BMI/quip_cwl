FROM sbubmi/test_segmentation:latest
MAINTAINER Tahsin Kurc

RUN yum -y install python python-devel python-pip && \
    curl --silent --location https://rpm.nodesource.com/setup_7.x | bash - && \
    yum -y install nodejs

RUN npm install -g forever && \
    pip install cwlref-runner && \
    wget https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    chmod 0755 jq-linux64 && mv jq-linux64 /usr/local/bin/. 

WORKDIR /root

RUN git clone -b develop https://github.com/SBU-BMI/quip_cwl.git && \
    cd quip_cwl && \
    npm install
 
ENV PATH=$PATH:"/root/quip_cwl/bin"
ENV PATH=$PATH:"./"

WORKDIR /root/quip_cwl

CMD ["node","worker_cwl.js"]
