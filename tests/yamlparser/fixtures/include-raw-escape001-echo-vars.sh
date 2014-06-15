#!/bin/bash
#
# test script containing some variables to show how you can include scripts
# into job template definitions provided you use the include-raw-escaped tag

MSG="hello world"

[[ -n "${MSG}" ]] && {
    # this next section is executed as one
    echo "${MSG}"
    exit 0
}
