#!/bin/sh
confirm() {
    read -r -p "${1:-Are you sure? [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

confirm "This script will expose \"${PWD}\" to an assist-assessment container. Do you want to continue? [y/n] " && \
docker run -it --rm -v "$PWD":/workingDir assist-assessment python3 /scriptDir/assistAssessment.py $@