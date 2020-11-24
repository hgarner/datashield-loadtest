FROM ubuntu:18.04

# set locale encodings otherwise pipenv install fails
ENV LC_ALL=C.UTF-8 
ENV LANG=C.UTF-8

# sort out timezome
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get -y update
RUN apt-get install -y gnupg software-properties-common

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
RUN apt-add-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/'

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential libcurl4-gnutls-dev libxml2-dev libssl-dev
RUN apt-get install -y r-base 
RUN apt-get install -y python3.6 python3-pip python3-setuptools python3-dev
RUN pip3 install pipenv

COPY . /datashield_loadtest
WORKDIR /datashield_loadtest
RUN ls

# install python reqs to system (not venv as not required in docker)
# deploy causes abort of lockfile out of date
RUN pipenv install --system --deploy
#RUN pipenv shell

RUN Rscript R/requirements.r
