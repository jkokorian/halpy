import inspect
import click
import jinja2
import yaml

def indent(lines, amount=4, ch=' '):
    padding = amount * ch
    return padding + ('\n'+padding).join(lines.split('\n'))

class ClassBuilder(object):
    def __init__(self):
        self._name = "Proxy"
        self._methods = []


    def set_name(self,name):
        self._name = name[0].capitalize() + name[1:]

    def add_method(self,name,argstring):
        method = dict(name=name,argstring=argstring)
        self._methods.append(method)


    def build_string(self):
        class_header = "class %s(object):\n" % self._name

        method_strings = [ProxyBuilder.build_method_string(method['name'], method['argstring']) for method in self._methods]

        class_body = "\n\n".join([indent(ms) for ms in method_strings])
        
        if not method_strings:
            class_body = "\n    pass\n"
        
        return class_header+class_body

    @staticmethod
    def build_method_string(name,argstring,bodystring="pass"):
        argstring = argstring\
            .strip('(')\
            .strip(')')\
            .replace('self','')\
            .strip(',')

        if len(argstring) > 0:
            argstring = "self, " + argstring
        else:
            argstring = "self"


        method_header = "def %s(%s):" % (name,argstring)

        method_body = indent(bodystring)

        return "\n".join([method_header,method_body])
        
        
proxyClassSkeletonTemplateString = \
"""
class {{className}}(object):
    def __init__(self):
        self.target = None
        
        
    # property definitions
    {% for s in propertySpecs %}
    {% if accessorType is equalto 'property' %}
    @property
    def {{s['propertyName']}}(self):
    {% else %}
    def get_{{s['propertyName']}}(self):
    {% endif %}
        return self.target.{{s['getter']['name']}}()
    
    {% if s['setter'] is not none %}
    {% if accessorType is equalto 'property' %}
    @{{s['propertyName']}}.setter
    {% endif %}
    def set_{{s['propertyName']}}(self, value):
        self.target.{{s['setter']['name']}}(value)
        
    {% endif %}
    {% endfor %}
    
    
    # method definitions
    {% for methodSpec in methodSpecs %}
    def {{methodSpec['name']}}():
        pass
    {% endfor %}
"""

proxyServiceTemplateString = \
"""
import argparse
import zmq

from tinyrpc.transports.zmq import ZmqServerTransport
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import RPCDispatcher,public

from tinyrpc.server import RPCServer

from os import system
class {{className}}Service(object):
    def __init__(self):
        self.target = None
        
        
    # property definitions
    {% for s in propertySpecs %}
    @public    
    def get_{{s['propertyName']}}(self):
        return self.target.{{s['getter']['name']}}()
    
    {% if s['setter'] is not none %}
    @public    
    def set_{{s['propertyName']}}(self, value):
        self.target.{{s['setter']['name']}}(value)    
    {% endif %}
    {% endfor %}
    
    
    # method definitions
    {% for methodSpec in methodSpecs %}
    def {{methodSpec['name']}}():
        pass
    {% endfor %}
    
    

if __name__=="__main__":
    
    system("Title "+ "{{windowTitle}}")

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--service-port","-p",dest="servicePort",type=int,default=5070)
    parser.add_argument("--service-ip",dest="serviceIP",type=str,default="127.0.0.1")
    
    args = parser.parse_args()
        
    ctx = zmq.Context()
    service = {{className}}Service()
    
    dispatcher = RPCDispatcher()
    dispatcher.register_instance(service)
    
    endpoint = 'tcp://%s:%i' % (args.serviceIP,args.servicePort)
    transport = ZmqServerTransport.create(ctx, endpoint)
    print "serving requests at %s" % endpoint
    
    
    rpc_server = RPCServer(
        transport,
        JSONRPCProtocol(),
        dispatcher
    )
    
    rpc_server.serve_forever()
"""

qtProxyClassSkeletopString = \
"""
class {{className}}(QObject):

    {{s['propertyName']}}Changed = pyqtSignal(s['propertyType'])

    def __init__(self,parent=None):
        QObject.__init__(self,parent=parent)
        self.target = None
        
    # property definitions
    {% for s in propertySpecs %}
    def {{s['propertyName']}}(self):
        return self.target.{{s['getter']['name']}}()
    
    {% if s['setter'] is not none %}
    def set_{{s['propertyName']}}(self, value):
        self.target.{{s['setter']['name']}}(value)
    {% endif %}
    {% endfor %}
    
    
    # method definitions
    {% for methodSpec in methodSpecs %}
    def {{methodSpec['name']}}():
        self.target.{{methodSpec['name]}}()
    {% endfor %}
"""



proxyClassSkeletonTemplate = jinja2.Template(proxyClassSkeletonTemplateString)
        
def getTemplateClassSpec(templateCls):
    memberDict = {m[0]: m[1] for m in inspect.getmembers(templateCls,predicate=inspect.ismethod)}
    
    constructor = memberDict['__init__'] if "__init__" in memberDict.keys() else None
    constructorArgs = inspect.getargspec(constructor)

    publicMemberNames = [key for key in memberDict if not key.startswith('_')]    

    methodSpecs = {}
    getterSpecs = {}
    setterSpecs = {}

    for name in publicMemberNames:
        m = memberDict[name]
        if name.lower().startswith("get"):
            getterSpecs[name[3:].strip("_")] = {'name': name, 'method': m}
        elif name.lower().startswith("set"):
            setterSpecs[name[3:].strip("_")] = {'name': name, 'method': m}
        else:
            methodSpecs[name] = {'name': name, 'method': m}
    
    propertySpecs = []

    for propertyName in set(getterSpecs.keys() + setterSpecs.keys()):
        propertySpec = {'propertyName': propertyName[0].lower() + propertyName[1:],
                        'getter': getterSpecs[propertyName] if propertyName in getterSpecs.keys() else None,
                        'setter': setterSpecs[propertyName] if propertyName in setterSpecs.keys() else None,
                        'propertyType': 'float'}
        propertySpecs.append(propertySpec)
        
    return {'propertySpecs': propertySpecs, 'methodSpecs': methodSpecs.values()}
        
def generateProxyTemplateSpec(templateCls):
    spec = getTemplateClassSpec(templateCls)
    click.echo(yaml.dump(spec))

    

def generateClassProxySkeleton(templateCls):
    proxyClassSkeletonString = proxyClassSkeletonTemplate.render(className=templateCls.__name__ + "Proxy", **getTemplateClassSpec(templateCls))
    click.echo(proxyClassSkeletonString)
















