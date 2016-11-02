name: timeout-wrapper
wrappers:
    - timeout:
        fail: true
        elastic-percentage: 150
        elastic-default-timeout: 90
        type: elastic
