- copyartifact: &copytarball
    project: foo
    filter: "*.tar.gz"
    target: /home/foo
    which-build: last-successful
    optional: true
    flatten: true
    parameter-filters: PUBLISH=true
- copyartifact:
    <<: *copytarball
    project: bar
    which-build: specific-build
    build-number: 123
