#!/bin/bash
#
# version 1.2 of the echo vars script

MSG="hello world"
VERSION="1.2"

[[ -n "${MSG}" ]] && {
    # this next section is executed as one
    echo "${MSG}"
    echo "version: ${VERSION}"
    exit 0
}
