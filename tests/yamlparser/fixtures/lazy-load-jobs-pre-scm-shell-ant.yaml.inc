name: pre-scm-shell-ant
wrappers:
    - pre-scm-buildstep:
        - shell: |
            #!/bin/bash
            echo "Doing somethiung cool"
        - shell: |
            #!/bin/zsh
            echo "Doing somethin cool with zsh"
        - ant:
            targets: "target1 target2"
            ant-name: "Standard Ant"
        - inject:
            properties-file: example.prop
            properties-content: EXAMPLE=foo-bar
