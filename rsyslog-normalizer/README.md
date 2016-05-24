
# The tool to test rsyslog normalizer

This is work in progress. The tools is quite dumb for the moment and not really scalable, but it gets some work done.

## Usage
send data to rsyslog-normalizer:
> python parse-test.py send rsyslog-server.local 10514
where
* rsyslog-server.local - the rsyslog server that does the normalization
* 10514 - port

query elasticsearch for results:
> python parse-test.py query http://elasticsearch:80 100
where  
* http://elasticsearch:80 is the URL of ElasticSearch server  
* 100 is the seed output of data sent.

## TODO
* Fine a proper framework and use it
* Move all tests to configs

