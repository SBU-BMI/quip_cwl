FROM sbubmi/test_segmentation:latest
MAINTAINER Tahsin Kurc

RUN yum -y install python python-devel python-pip && \
    curl --silent --location https://rpm.nodesource.com/setup_7.x | bash - && \
    yum -y install nodejs

RUN npm install -g forever && \
    pip install cwlref-runner

WORKDIR /root

RUN git clone https://github.com/SBU-BMI/quip_cwl.git && \
    cd quip_cwl; npm install;
 
ENV PATH=$PATH:/root/quip_cwl/bin

CMD ["node","worker_cwl.js"]
