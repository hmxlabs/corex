FROM ubuntu:22.04
RUN echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
RUN echo 'APT::Install-Recommapprunnerends "0";' >> /etc/apt/apt.conf.d/00-docker
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3 openssl\
  && rm -rf /var/lib/apt/lists/*
RUN useradd -ms /bin/bash corexrunner
USER corexrunner
WORKDIR /home/corexrunner
RUN mkdir --parents /home/corexrunner/corex
RUN mkdir --parents /home/corexrunner/corex/bin
COPY --chown=corexrunner:corexrunner corex.tar.gz /home/corexrunner
RUN tar -xf /home/corexrunner/corex.tar.gz -C /home/corexrunner/corex
RUN rm /home/corexrunner/corex.tar.gz
COPY --chown=corexrunner:corexrunner corex-bin-8-linux-x86_64.tar.gz /home/corexrunner/corex
RUN tar -xf /home/corexrunner/corex/corex-bin-8-linux-x86_64.tar.gz -C /home/corexrunner/corex/bin
WORKDIR /home/corexrunner/corex
VOLUME /home/corexrunner/corex/output
ENTRYPOINT ["python3", "/home/corexrunner/corex/corex.py", "--ore-dir", "/home/corexrunner/corex/bin/"]