#!/bin/bash
#
# version 1.1 of the echo vars script

MSG="hello world"
VERSION="1.1"

[[ -n "${MSG}" ]] && {
    # this next section is executed as one
    echo "${MSG}"
    echo "version: ${VERSION}"
    exit 0
}
