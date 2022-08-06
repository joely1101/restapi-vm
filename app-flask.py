#!/usr/bin/python3
from xmlrpc.client import boolean
from flask import Flask ,jsonify
from flask import request
from vmnetwork import network
from vmdomain import domain
import json
#from flasgger import Swagger
from flask_cors import CORS
import log 

app = Flask(__name__)
#swagger = Swagger(app,template_file='swagger-specs.yml')
CORS(app)
app.config['JSON_SORT_KEYS'] = False

prefix="vmapi"

class VirtMachine(network,domain):
    def __init__(self):
        self.connect()

vm=VirtMachine()



def msg_jsonify(ret,booltype=False):
    jret={}
    logs=log.logGet()
    print(f"======={logs}")
    if not booltype:
        if ret != None:
            jret['result']="Success"
            jret['message']=logs
            jret['data']=ret
        else:
            jret['result']="Failure"
            jret['message']=logs
    else:
        if ret == True:
            jret['result']="Success"
            jret['message']=logs
        else:
            jret['result']="Failure"
            jret['message']=logs
    return jsonify(jret)

def msg_jsonify_bool(ret):
    return msg_jsonify(ret,True)

@app.route("/vmapi/networks")
def app_networks():
    net=vm.ListNetworks()
    return msg_jsonify(net)
@app.route("/vmapi/network/create",methods=['POST'])
def app_network_create():
    """
    {
        name:"name"
        type:"sriov/vnet/macvtap"
        interface:"eth1"
        bridge:"br-vm0"
        bridgetype:"nat|bridge"
        ipaddr:"10.2.2.2"
        dhcpserver:"on/off"
    }
    """
    ret=None
    data = request.json
    if data == None or request.headers.get('Content-Type') != 'application/json':
        log.log("Invalid formate, json only")
        return msg_jsonify_bool(False)

    name = data.get('name')
    if name == None:
        log.log("No name specify!!")
        return msg_jsonify_bool(False)
    
    if name == None:
        log.log("No name specify!!")
        return msg_jsonify_bool(False)

    type = data.get('type')
    if type == None:
        log.log("No type specify!!")
        return msg_jsonify_bool(False)
    
    if type == 'sriov':
        interface=data.get('interface')
        if interface == None:
            log.log("Invalid interface!!")
            return msg_jsonify_bool(False)
        ret=vm.CreateNetwork_sriov(name,interface)
    elif type == 'macvtap':
        interface=data.get('interface')
        if interface == None:
            log.log("Invalid interface!!")
            return msg_jsonify_bool(False)
        ret=vm.CreateNetwork_macvtap(name,interface)

    elif type == 'vnet':
        bridge=data.get('bridge')
        ipaddr=data.get('ipaddr')
        bridgetype=data.get('ipaddr',"nat")
        dhcpserver=data.get('dhcpserver',"off")
        dhcpon=True if dhcpserver == 'off' else False
        print(dhcpon)
        ret=vm.CreateNetwork_vnet(name,ipaddr,bridge,bridgetype,dhcpon)
    else:
        print(f"unknow type {type}")
    return msg_jsonify(ret)

@app.route("/vmapi/network/delete",methods=['POST'])
def app_network_delete():
    data = request.json
    if data == None or request.headers.get('Content-Type') != 'application/json':
        log.log("Invalid formate, json only")
        return msg_jsonify_bool(False)

    name = data.get('name')
    if name == None:
        log.log("No name specify!!")
        return msg_jsonify_bool(False)
    
    ret=vm.DeleteNetwork(name)
    if ret:
        log.log(f"Delete {name} success.")
    else:
        log.log(f"Delete {name} failed.")
    
    return msg_jsonify_bool(ret)

@app.route("/vmapi/network/<name>")
def app_network_byname(name):
    net=vm.GetNetwrok(name)
    return msg_jsonify(net)

@app.route("/vmapi/domains")
def app_domains():
    dm=vm.ListDomains()
    return msg_jsonify(dm)

@app.route("/vmapi/domain/<name>")
def app_domain_byname(name):
    dm=vm.GetDomain(name)
    return msg_jsonify(dm)

@app.route("/vmapi/domain/delete",methods=['POST'])
def app_domain_delete():
    data = request.json
    if data == None or request.headers.get('Content-Type') != 'application/json':
        log.log("Invalid formate, json only")
        return msg_jsonify_bool(False)

    name = data.get('name')
    if name == None:
        log.log("No name specify!!")
        return msg_jsonify_bool(False)
    
    ret=vm.DeleteDomain(name)
    if ret:
        log.log("delete success.")
    else:
        log.log("delete fail.")
    
    return msg_jsonify_bool(ret)

@app.route("/vmapi/domain/create",methods=['POST'])
def app_domain_create():
    """
    {
        name:"name"
        disk:"/vm/cirros.img"
        cpulist:"1,2,3"
        memory:"1024"
        networks:[
            {"source":"network_name"},
            {"mac":"00:00:00:00:00:22"}
        ]        
    }
    """
    data = request.json
    if data == None or request.headers.get('Content-Type') != 'application/json':
        log.log("Invalid formate, json only")
        return msg_jsonify_bool(False)

    name = data.get('name')
    if name == None:
        log.log("No name specify!!")
        return msg_jsonify_bool(False)
    
    
    disk = data.get('disk')
    if name == None:
        log.log("No disk specify!!")
        return msg_jsonify_bool(False)
    
    if data.get('cpulist') == None:
        data['cpulist']='7'
    if data.get('memory') == None:
        data['cpulist']='1024'
    if data.get('network') == None:
        data['network']=[]
    
    dm=vm.CreateDomain(name,disk,data['cpulist'],data['memory'],netlist=data['network'])
    
    return msg_jsonify(dm)


app.run(host='0.0.0.0',port=9001,debug=True)

