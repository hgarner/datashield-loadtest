FROM ubuntu:18.04

COPY . /datashield_loadtest
WORKDIR /datashield_loadtest

# sort out timezome
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get -y update
RUN apt-get install -y gnupg software-properties-common
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61
RUN echo 'deb https://dl.bintray.com/obiba/deb all main' >> /etc/apt/sources.list.d/obiba.list
RUN apt-get update -y
RUN apt-get install -y python3-distutils
RUN apt-get install -y opal-python-client

RUN apt-get install -y netcat

RUN chmod +x opal_import_cnsim.sh
ENTRYPOINT ["./opal_import_cnsim.sh"]
