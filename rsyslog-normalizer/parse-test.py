import sys
import socket
import datetime
import json
import elasticsearch
import random
import time

def get_matches(es_server, debug=False):
    es = elasticsearch.Elasticsearch(es_server)
    indices = elasticsearch.client.IndicesClient(es)
    query = {
         "filter": {
             "term": {
                "msgid": str(seed)
             }
         }
    }
    date = datetime.datetime.today()
    index_list = ["v2016.03.10.0-viaq-%s" %(str(date).split(' ')[0].replace('-','.')) ]

    matches = es.search(index_list, body=query, size=100, explain=True)
    print "Matches for: query: %s | index:  %s" %(query, index_list)
    #print matches
    return matches


def send_log(sock, cee):
    appnames = {
       0: 'kernel',
       1: 'NetworkManager',
       2: 'docker',
       3: 'apache',
       4: 'ns-slapd',
       5: 'audit',
       6: 'sudo',
       7: 'CROND'
    }

    hsh = {}
    hsh['pri'] = 10
    hsh['app'] = appnames[5]
    hsh['ts'] = datetime.datetime.utcnow().isoformat() + "Z"
    hsh['hn'] = 'host.example.test'
    hsh['msgid'] = seed
    hsh['ver'] = 1
    hsh['pid'] = 1000
    hsh['cee'] = cee
    msg = '<%(pri)d>%(ver)d %(ts)s %(hn)s %(app)s %(pid)d %(msgid)s - @cee:%(cee)s' % hsh
    if sock:
        rv = sock.sendto(msg, (ip, port))
        print "message is %s " % msg
        print "rv %s" % rv
    else:
        print msg

def send_different_hostname(sock):
    # Different _HOSTNAME
    hsh = {}
    hsh['_HOSTNAME'] = 'not_an_example.host'
    hsh['msg'] = 'Hostname is different'
    cee = json.dumps({'msg': hsh['msg'],
                      '_HOSTNAME': hsh['_HOSTNAME']})
    send_log(sock, cee)

def test_different_hostname(hits):
    for hit in hits:
        if not 'CEE' in hit['_source']:
            continue
        if '_HOSTNAME' in hit['_source']['CEE']:
            assert(hit['_source']['CEE']['_HOSTNAME'] == 'not_an_example.host')
            return True
    return False

def send_simple_tag(sock):
    # Different tag exists
    hsh = {}
    hsh['tags'] = 'example-tag1 example-tag2'
    hsh['msg'] = 'Tag exists'
    cee = json.dumps({'msg': hsh['msg'],
                      'tags': hsh['tags']})
    send_log(sock, cee)

def test_simple_tag(hits):
    for hit in hits:
        if 'tags' in hit['_source'] and hit['_source'].get('tags') == 'example-tag1 example-tag2':
            return True
    return False

def send_same_systemd_message(sock):
    # Same message from systemd exists
    msg = 'Same message in msg and MESSAGE must be collapsed'
    systemd_msg = 'Same message in msg and MESSAGE must be collapsed'    
    cee = json.dumps({'msg': msg,
                      'MESSAGE': systemd_msg})
    send_log(sock, cee)

def test_same_systemd_message(hits):
    res = False
    for hit in hits:
        if 'MESSAGE' in hit['_source']['CEE']:
            return False
        if hit['_source'].get('message') == 'Same message in msg and MESSAGE must be collapsed':
            res = True
    return res

def send_diff_systemd_message(sock):
    # Different message from systemd exists
    msg = 'Different message in msg and MESSAGE must leave this as unparsed in pipeline_metadata.normalizer.original_raw_message'
    systemd_msg = 'Different message in msg and MESSAGE must leave this in the message field'
    cee = json.dumps({'msg': msg,
                      'MESSAGE': systemd_msg})
    send_log(sock, cee)

def test_diff_systemd_message(hits):
    for hit in hits:
        if hit['_source'].get('message') == 'Different message in msg and MESSAGE must leave this in the message field':
            if 'MESSAGE' in hit['_source']['CEE']:
                return False
            if 'Different message in msg and MESSAGE must leave this as unparsed in pipeline_metadata.normalizer.original_raw_message' in hit['_source']['pipeline_metadata'].get('normalizer').get('original_raw_message'):
                return True
    return False

def send_ipaddr4_exists(sock):
    # ipaddr4 field exists
    msg = 'ipaddr4 field is set on the collector'
    ip = '192.168.0.1'
    cee = json.dumps({'msg': msg,
                      'ipaddr4': ip})
    send_log(sock, cee)

def test_ipaddr4_exists(hits):
    for hit in hits:
        if 'ipaddr4' in hit['_source']:
            return True
    return False

def send_PID_exists(sock):
    # TODO: There should be various testcases for $!_PID, $procid, $!pid fields each might be "-", non-existent, equal to a "peer", not equal to a "peer"
    msg = 'systemd _PID field exists set on the collector'
    pid = '192'
    cee = json.dumps({'msg': msg,
                      '_PID': pid})
    send_log(sock, cee)

def test_PID_exists(hits):
    for hit in hits:
        if 'systemd' in hit['_source']:
            if 't' in hit['_source']['systemd']:
                if '192' ==  hit['_source']['systemd']['t'].get('PID'):
                    return True
    return False

def send_pipeline_metadata(sock):
    # pipeline_metadata field exists
    msg = 'pipeline_metadata section exists in this message from collector'
    pipeline_metadata = {'other' : 'some other value',
                         'collector' : { 'name': 'collector_name',
                                         'ipaddr4': '10.110.10.10',
                                         'inputname': 'imjournal',
                                         'raw_original_message': 'This is the RAW message from the collector!'}}
    cee = json.dumps({'msg': msg,
                      'pipeline_metadata': pipeline_metadata})
    send_log(sock, cee)

def test_pipeline_metadata(hits):
    for hit in hits:
        if 'collector' in hit['_source']['pipeline_metadata']:
            if (hit['_source']['pipeline_metadata'].get('other') == 'some other value' and
               hit['_source']['pipeline_metadata']['collector'].get('name') == 'collector_name' and
               hit['_source']['pipeline_metadata']['collector'].get('ipaddr4') == '10.110.10.10' and
               hit['_source']['pipeline_metadata']['collector'].get('inputname') == 'imjournal' and
               hit['_source']['pipeline_metadata']['collector'].get('raw_original_message') == 'This is the RAW message from the collector!'):
                return True
    return False

def print_test(test, res):
    print test.__name__ + " " + str(test(res['hits']['hits']))

def send_test_data():

    sock = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    send_different_hostname(sock)
    send_simple_tag(sock)
    send_same_systemd_message(sock)
    send_diff_systemd_message(sock)
    send_ipaddr4_exists(sock)
    send_pipeline_metadata(sock)
    send_PID_exists(sock)

    sock.close()

if len(sys.argv) > 1:
    action = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])
    #es_server = sys.argv[3]

if action == 'send':
    seed = random.randint(0,100000)
    send_test_data()
    print "Seed is: %s" % seed
elif action == 'query':
    seed = port
    results =  get_matches(ip)
    print_test(test_different_hostname, results)
    print_test(test_simple_tag, results)
    print_test(test_same_systemd_message, results)
    print_test(test_diff_systemd_message, results)
    print_test(test_ipaddr4_exists, results)
    print_test(test_pipeline_metadata, results)
