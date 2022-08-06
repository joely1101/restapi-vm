#!/usr/bin/python3
import libvirt
import xmltodict
from connection import lvconn
import json
import sys
import log
class network(lvconn):
    def __init__(self):
        self.connect()
    
    def GetNetwrokNode(self,name,quiet=False):
        network=None
        try:
            network=self.conn.networkLookupByName(name)
        except libvirt.libvirtError as e:
            if quiet == False:
                log.log(repr(e))
                print(repr(e))
        
        return network

    def GetNetwrok(self,name):
        network=self.GetNetwrokNode(name)
        if network:
            return xmltodict.parse(network.XMLDesc(0))
        else:
            log.log(f"Network '{name}' not found")
        return None

    def ListNetworks(self):
        listnw=[]
        networks = self.conn.listNetworks()
        for name in networks:
                network=self.GetNetwrokNode(name)
                if network:
                    node=xmltodict.parse(network.XMLDesc(0))
                    listnw.append(node)        
        return listnw

        
    def CreateNetwork_xml(self,xml,start=True,autostart=True):
        node=xmltodict.parse(xml)
        network=self.GetNetwrokNode(node['network']['name'],True)
        if network == None:
            network = self.conn.networkDefineXML(xml)
        else:
            log.log("network already exist")
            print("network already exist")
            
        if network == None:
            log.log("Failed to define a virtual network")
            print('Failed to define a virtual network')
            return network
        

        if network.isActive()==1:
            network.destroy()
        
        if start:
            network.create()
        
        network.setAutostart(autostart)
        
        return xmltodict.parse(network.XMLDesc(0))

    def CreateNetwork_sriov(self,name,interface):
        xml=f"""
    <network>
        <name>{name}</name>
        <forward mode='hostdev' managed='yes'>
            <pf dev={interface}/>
        </forward>
    </network>
    """
        return self.CreateNetwork_xml(xml)
    
    def CreateNetwork_macvtap(self,name,interface):
        xml=f"""
    <network>
    <name>{name}</name>
    <forward mode="bridge">
        <interface dev="{interface}"/>
    </forward>
    </network>
    """
        return self.CreateNetwork_xml(xml)

    def CreateNetwork_vnet(self,name,ipaddr,br_name=None,bridgetype='nat',dhcp=False):
        if br_name != None:
            #br_str=f'<bridge name="{br_name}" stp='on' delay='0'/>'
            br_str=f'<bridge name="{br_name}"/>'
        if dhcp:
            dhcp_str='<dhcp></dhcp>'
        if bridgetype == 'nat':
            xml="""
    <network>
    <name>{name}</name>
    <forward mode='nat'>
        <nat>
        <port start='1024' end='65535'/>
        </nat>
    </forward>
    {br_str}
    <ip address="{ipaddr}" netmask='255.255.255.0'>
    {dhcp_str}
    </ip>
    </network>        
    """
        else:
            xml=f"""
    <network>
        <name>${name}</name>
            <forward mode="bridge" />
            {br_str}
    </network> 
    """
        return self.CreateNetwork_xml(xml)

    def DeleteNetwork(self,myname):
        network = self.GetNetwrokNode(myname)
        if network:
            if network.isActive()==1:
                network.destroy()
            network.undefine()                        
            return True
        return False
