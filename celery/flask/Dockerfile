FROM sbubmi/test_segmentation:latest
MAINTAINER Tahsin Kurc

RUN yum -y install python python-devel python-pip && \
    curl --silent --location https://rpm.nodesource.com/setup_7.x | bash - && \
    yum -y install nodejs

RUN pip install --upgrade pip && \
    pip install celery flask flower gevent pyyaml cwlref-runner && \
    yum -y install curl wget vim && \
    wget https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64 && \
    chmod 0755 jq-linux64 && mv jq-linux64 /usr/local/bin/. 

ADD . /root/server/
WORKDIR /root/server
RUN cp bin/* /usr/local/bin/.

CMD ["/root/server/run.sh"]
