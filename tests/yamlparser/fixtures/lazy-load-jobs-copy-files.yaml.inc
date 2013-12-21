name: copy-files
wrappers:
    - copy-to-slave:
        includes:
        - file1
        - file2*.txt
        excludes:
        - file2bad.txt
