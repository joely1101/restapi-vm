#!/usr/bin/python3
import lxml.etree as ET
import xmltodict
import json
from collections import OrderedDict as od
from connection import lvconn
import libvirt
import log
vm_xml_template="xml_tmpl/vm.xml"
def gen_network_interface(source,mac=None):
    if mac != None:
        macstr=f"<mac address='{mac}'/>"
    else:
        macstr=""
    ss=f"""
    <interface type='network'>
      {macstr}
      <source network='{source}'/>
      <model type='virtio'/>
    </interface>
    """
    newinf=xmltodict.parse(ss)
    return newinf

def get_state_string(state):
    statestr="Unknow"
    if state == libvirt.VIR_DOMAIN_NOSTATE:
        statestr="NoState"
    elif state == libvirt.VIR_DOMAIN_RUNNING:
        statestr="Running"
    elif state == libvirt.VIR_DOMAIN_BLOCKED:
        statestr="Blocked"
    elif state == libvirt.VIR_DOMAIN_PAUSED:
        statestr="Pause"
    elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
        statestr="Shutdown"
    elif state == libvirt.VIR_DOMAIN_SHUTOFF:
        statestr="Shutoff"
    elif state == libvirt.VIR_DOMAIN_CRASHED:
        statestr="Crashed"
    elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
        statestr="PMSUSPENDED"
    return statestr

class domain(lvconn):
    def __init__(self):
        self.connect()

    def LoadJsonFile(self,file=None):    
        dictData=None
        if file == None:
            return dictData
        with open(file) as d:
            dictData = json.load(d)
        return dictData
    
    def LoadJsonStr(self,jstring):
        return json.loads(jstring)
    
    def LoadXmlFile(self,file=None):
        if file == None:
            return None
        tree = ET.parse(file)
        return tree

    def GetDomainNode(self,name):
        domain=None
        try:
            domain=self.conn.lookupByName(name)
        except libvirt.libvirtError as e:
            log.log(repr(e))
            #print(repr(e))
        return domain
    
    def GetDomain(self,name):
        domainX=self.GetDomainNode(name)
        if domainX == None:
            log.log(f"{name} not found")
            return None
        domain=xmltodict.parse(domainX.XMLDesc(0))
        if domain:
            retdom={}
            retdom['name']=domain['domain']['name']
            retdom['vcpu']=domain['domain']['vcpu']['#text']
            retdom['memory']=f"{domain['domain']['memory']['#text']} {domain['domain']['memory']['@unit']}"
            retdom['disk']=domain['domain']['devices']['disk']['source']['@file']
            intfs=domain['domain']['devices'].get('interface')
            

            if type(intfs) == dict:
                #change to list
                oldifs=intfs
                intfs=[]
                intfs.append(oldifs)

            if intfs:
                retdom['network']=[]
                for intf in intfs:
                    intfa={}
                    intfa['type']=intf['@type']
                    intfa['name']=intf['source']['@network']
                    intfa['mac']=intf['mac']['@address']
                    intfa['target']=intf['target']['@dev']
                    retdom['network'].append(intfa)
            
            return retdom
        else:
            log.log(f"domain '{name}' not found")
        return domain
    
    def CreateDomain(self,name,disk,cpulist,memory,autostart=True,netlist=None):
        try:
            dt=None
            dom=None
            cpucount=len(cpulist.split(","))
            with open(vm_xml_template) as fd:
                dt=xmltodict.parse(fd.read())
                
            if dt == None:
                return None
            dt['domain']['name']=name
            dt['domain']['devices']['disk']['source']['@file']=disk
            dt['domain']['memory']['@unit']='MiB'
            dt['domain']['memory']['#text']=f"{memory}"
            dt['domain']['vcpu']['@cpuset']=cpulist
            dt['domain']['vcpu']['#text']=f"{cpucount}"
            
            if netlist and len(netlist) > 0:
                #if 'interface' not in dt['domain']['devices']:
                if dt['domain']['devices'].get('interface') == None:
                    dt['domain']['devices']['interface']=[]
                for net in netlist:
                    newintf=gen_network_interface(net.get('source'),net.get('mac'))
                    dt['domain']['devices']['interface'].append(newintf['interface'])
            
            xml_format= xmltodict.unparse(dt,pretty=True)
            #print(f"{xml_format}")
            #with open("a.xml","a+") as ff:
            #    ff.write(xml_format)
            dom = self.conn.defineXMLFlags(xml_format, 0)
            if dom == None:
                log.log("Unable to define persistent guest configuration.")
                print('Unable to define persistent guest configuration.', file=sys.stderr)
                return None
            if dom.create() < 0:
                log.log('Can not boot guest domain')
            
            dom.setAutostart(autostart)
        except libvirt.libvirtError as e:
            log.log(repr(e))
            log.log("domain create fail.")
            if dom:
                dom.undefine()
                dom=None
        if dom:
            return self.GetDomain(name)
        return None

    def ActionDomain(self,name,action='stop'):
        domain=self.GetDomainNode(name)
        if domain:
            if action == 'stop':
                domain.destroy()
            elif action == 'delete':
                domain.undefine()
            elif action == 'start':
                domain.create()
            return True
        return False

    def DeleteDomain(self,name):
        try:
            domain=self.GetDomainNode(name)
            if domain:
                if domain.isActive():
                    domain.destroy()
                domain.undefine()
                return True
            else:
                log.log("domain not found")
        except libvirt.libvirtError as e:
            log.log(repr(e))

        return False
        
    def ListDomains(self):
        retdms=[]
        domains = self.conn.listAllDomains(0)
        for domain in domains:
            dm={}
            state=get_state_string(domain.info()[0])
            dm['name']=domain.name()
            dm['state']=state
            #print(f"info {dm}")
            retdms.append(dm)
        return retdms
        