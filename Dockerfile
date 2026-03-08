FROM flink:2.2.0

USER root

RUN apt-get update -y && \
    apt-get install -y \
      python3 \
      python3-pip \
      python3-dev \
      python3-venv \
      openjdk-17-jdk-headless \
      && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install apache-flink==2.2.0 beautifulsoup4
RUN chown -R flink:flink /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Setup App
USER flink
RUN mkdir /opt/flink/usrlib
COPY jobs/main.py /opt/flink/usrlib/main.py
