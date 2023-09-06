from json import load as loadJson
import xml.etree.ElementTree as ET
import os
import shutil
import subprocess

rootDir = os.getcwd()

class Config:
    packageName='mockservice'
    artifactId='mockservice'
    groupId='com.ws'
    wsdlFile=""
    description="Mock service"
    endpoint="endpoint"
    path=''

    def __init__(self,dict) -> None:
        for key in dict:
            self.__setattr__(key,dict[key])

global config

# Copies the wsdl file to resources folder.
def copyWsdlFile():
    if not os.path.exists(f"{config.packageName}\\src\\main\\resources\\wsdl"):
        os.mkdir(f"{config.packageName}\\src\\main\\resources\\wsdl")
    shutil.copy2(f"{config.wsdlFile}",f"{config.packageName}\\src\\main\\resources\\wsdl\\")


# Adds the necessary dependencies and plugins to the Project (pom.xml)
def addDependenciesAndPlugins():
    rawXMLdependencies = ["""
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web-services</artifactId>
            
            </dependency>    
            """,
            """
            <dependency>
                <groupId>org.apache.cxf</groupId>
                <artifactId>cxf-spring-boot-starter-jaxws</artifactId>
                <version>4.0.2</version>
            </dependency>

    """]

    rawXMLplugins = f"""
                <plugin>
                    <groupId>org.apache.cxf</groupId>
                    <artifactId>cxf-codegen-plugin</artifactId>
                    <version>4.0.2</version>
                    <executions>
                        <execution>
                            <id>generate-sources</id>
                            <phase>generate-sources</phase>
                            <configuration>
                                <sourceRoot>${{project.build.directory}}/generated-sources/cxf</sourceRoot>
                                <wsdlOptions>
                                    <wsdlOption>
                                        <wsdl>
                                            ${{project.basedir}}/src/main/resources/wsdl/{config.wsdlFile}
                                        </wsdl>
                                        <extraargs>
                                            <extraarg>-bareMethods</extraarg>
                                            <extraarg>-p</extraarg>
                                            <extraarg>{config.groupId}.{config.artifactId}</extraarg>
                                        </extraargs>
                                    </wsdlOption>
                                </wsdlOptions>
                            </configuration>
                            <goals>
                                <goal>wsdl2java</goal>
                            </goals>
                        </execution>
                    </executions>
                </plugin>

    """
    xmlns={
        'ns':"http://maven.apache.org/POM/4.0.0"
    }
    
    with open(f'{config.packageName}/pom.xml') as pom:
        ET.register_namespace('',xmlns.get('ns'))
        tree = ET.parse(pom)
        root = tree.getroot()

        dependecies = root.find('ns:dependencies',xmlns)
        if dependecies!=None:
            for rawXMLdependency in rawXMLdependencies:
                XMLdependency=ET.XML(rawXMLdependency)
                dependecies.append(XMLdependency)
        else:
            print("No Dependency in pom file \nQuit")
            exit(-1)
        
        plugins= root.find('ns:build',xmlns).find('ns:plugins',xmlns)
        if(plugins!=None):
            XMLplugins=ET.XML(rawXMLplugins)
            plugins.append(XMLplugins)

        tree.write(f"{config.packageName}\\pom.xml",xml_declaration=True,encoding="UTF-8")

# Runs the command spring init --build=maven,... with names given from the config file ... -p=jar -j=20 
def initSpring():
    springCliCommand=["spring", "init", "--build=maven" ,f'-a="{config.artifactId}"' ,f'-g="{config.groupId}"',f'-n="{config.packageName}"' ,f'--description="{config.description}"' ,'-p=jar' ,'-j=20' , config.packageName]
    subprocess.run(springCliCommand,shell=True)

# Runs the command "mvn generate-sources" in the terminal.
def buildMvn():
    os.chdir(config.packageName)
    mvnCommand=["mvn", "generate-sources"]
    subprocess.run(mvnCommand,shell=True)
    os.chdir(rootDir)

class OperationObj:
    #this will be lower cased
    operationName=''
    inputMessage=''
    outputMessage=''

    operationNameCapitalized=''
    inputMessageCapitalized=''
    outputMessageCapitalized=''


    def capitalizeMessages(self):
        self.inputMessageCapitalized=self.inputMessage[:1].upper()+self.inputMessage[1:]
        self.outputMessageCapitalized=self.outputMessage[:1].upper()+self.outputMessage[1:]
        self.operationNameCapitalized=self.operationName[:1].upper()+self.operationName[1:]
        
        self.inputMessage=self.inputMessage[:1].lower()+self.inputMessage[1:]
        self.outputMessage=self.outputMessage[:1].lower()+self.outputMessage[1:]
        self.operationName=self.operationName[:1].lower()+self.operationName[1:]
        
portName=''

# Removes the (target) name space of the names retrieved from WSDL file.
def removeNamespace(strVal):
    if strVal!=None:
        tmpStr = strVal.split(':', 1)
        if len(tmpStr) > 0: 
            strVal = tmpStr[1]
    return strVal

class messageObj:
    message=''
    input=''
    output=''

# Retrieves the java method and Class names from the WSDL file so that they match with the WSDL file.
# which are found through searching portType>operation> message> element
def findPortAndMethodNames():
    global portName
    tree = ET.parse(config.wsdlFile)
    root = tree.getroot()
    portTypeElem = root.find(".{*}portType")
    portName= portTypeElem.attrib.get("name")
    operationLst=portTypeElem.findall(".{*}operation")
    
    messages= root.findall("{*}message")
    operationObjs=[]
    for operation in operationLst:
        op=OperationObj()
        op.operationName=operation.attrib.get("name")
        tmpIn = removeNamespace(operation.find(".{*}input").attrib.get("message"))
        tmpOut=removeNamespace(operation.find(".{*}output").attrib.get("message"))
        for message in messages:
            if message.get("name") == tmpIn:
                op.inputMessage=removeNamespace(message[0].get("element"))
                inputFound=True
            elif message.get("name") ==tmpOut:
                op.outputMessage=removeNamespace(message[0].get("element"))
                if inputFound:
                    break
        op.capitalizeMessages()
        operationObjs.append(op)
    return operationObjs

# Creates the Config class which publishes the endpoint via a Bean.
def createConfigFile():
    javaCode=f"""package {config.groupId}.{config.artifactId}.config;
import {config.groupId}.{config.artifactId}.{portName}Impl;
import jakarta.xml.ws.Endpoint;
import org.apache.cxf.Bus;
import org.apache.cxf.jaxws.EndpointImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebServiceConfig {{
    @Autowired
    private Bus bus;

    @Bean
    public Endpoint endpoint(){{
        Endpoint endpoint = new EndpointImpl(bus, new {portName}Impl());
        endpoint.publish("/{config.endpoint}");
        return endpoint;
    }}
}}
"""
    config.path=f"{config.packageName}\\src\\main\\java\\"+'\\'.join(config.groupId.split('.')) +"\\"+config.artifactId

    if not os.path.exists(f"{config.path}\\config"):
        os.mkdir(f"{config.path}\\config")

    with open (f"{config.path}\\config\\WebServiceConfig.java",'w') as file:
        file.write(javaCode)
    
# Creates the Impl file for each portType/binding
# Each java method has the same structure
# Reads the response from a file, unmarshalls it to a java class, then marshalls it to respond.
def createImplFile(implMethods)->None:
    global portName
    javaImports=f"""package {config.groupId}.{config.artifactId};

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBElement;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Unmarshaller;

import javax.xml.transform.stream.StreamSource;
import java.io.File;

public class {portName}Impl implements {portName}{{
    """

    javaMethods=[]
    for method in implMethods:
        tmpCode=f"""
    @Override
    public {method.outputMessageCapitalized} {method.operationName}({method.inputMessageCapitalized} request) {{
        try{{
            File file = new File("..\\\\responses\\\\{method.outputMessage}.xml");
            JAXBContext jaxbContext = JAXBContext.newInstance({method.outputMessageCapitalized}.class);
            Unmarshaller jaxbUnmarshaller = jaxbContext.createUnmarshaller();
            JAXBElement<{method.outputMessageCapitalized}> jaxbElement =
                    (JAXBElement<{method.outputMessageCapitalized}>) jaxbUnmarshaller
                            .unmarshal(new StreamSource(file),{method.outputMessageCapitalized}.class);
            return jaxbElement.getValue();
        }}catch (JAXBException | RuntimeException e ){{
            e.printStackTrace();
        }}
        return new {method.outputMessageCapitalized}();
    }}
"""
        javaMethods.append(tmpCode)
    javaCode= javaImports + "\n".join(javaMethods)+"\n}"
    with open (f"{config.path}\\{portName}Impl.java",'w') as file:
       file.write(javaCode)

# Parses the config json file to the object "config".
def parseConfig()->None:
    with open('mock-service-config.json') as configFile:
        global config
        config=Config(loadJson(configFile))
        
# Writes appropriate response file names to a file namely "responseFileNames.txt"
def writeResponseFileNames(operations)->None:
    responseFileNamesLst=[]
    try:
        for op in operations:
            responseFileNamesLst.append(op.outputMessage)
        responseFileNamesStr="\n".join(responseFileNamesLst)

        with open("responseFileNames.txt",'w') as file:
            file.write(responseFileNamesStr)
    except Exception:
        print ("Error occured while writing the response file names to responseFileNames.txt.")
    

def main():
    parseConfig()
    initSpring()
    copyWsdlFile()
    addDependenciesAndPlugins()
    buildMvn()
    operations=findPortAndMethodNames()
    writeResponseFileNames(operations)
    createConfigFile()
    createImplFile(operations)

if __name__ == "__main__":
    main()

