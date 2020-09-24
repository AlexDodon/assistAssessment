FROM ubuntu

RUN apt-get update
RUN apt-get install -y ghc sbcl polyml python3

RUN mkdir "/scriptDir"
ADD "assistAssessment.py" "/scriptDir"

RUN mkdir "/workingDir"
WORKDIR "/workingDir"