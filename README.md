# SOAP Mock Webservice
This script creates a Spring Boot application, from a given WSDL file, by a configuration file, which accepts and responds from files that are specified in the WSDL file. More detailes explained below.

# Software Requirements
Tested with:
- Java 20
- Python 3.8 (or Later)
- Spring Boot Cli 3.1.2
- Apache Maven 3.9.3

And requires these applications to be on the Windows path.

May work with lower versions, but not fully tested.

# How to Run
Before running for the first time see **How to Use** section.

Can be run in a terminal, to create a Spring Boot project run:

    python .\createSoapWS.py

Then open up your favourite IDE, preferably Intellij IDEA, and run the Spring Boot project as usual, or run the following:
    
    mvn spring-boot:run

# How to Use

### Config File
- Fill in the config file namely `mock-service-config.json`.     Fields of the config file are self explanatory. 
    
    * *packageName, artifactId, groupId.*

    * *wsdlFile* is the location and the name of the WSDL file.
        
    * *description* is the description of the Project to be created,

    * *endpoint* is the endpoint to be published.

- You can run the script now or after adding responses.

### Responses
- Add your responses to *"responses"* folder
    * Responses folder must be in the same folder as the createMockWS.py i.e. it should be in the parent directory of the Spring Boot project.
    * In order to match the response files with the soap request,
    response file names should be named with the corresponding operation's the output message element in the WSDL file and should start with a lower case letter.

#### Example:
- Say we have the following operation in portType section of the WSDL file:

            <operation name="ListOfContinentsByName">
                <documentation>Returns a list of continents ordered by name.</documentation>
                <input message="tns:ListOfContinentsByNameSoapRequest"/>
                <output message="tns:ListOfContinentsByNameSoapResponse"/>
            </operation>

    And we have the message:

            <message name="ListOfContinentsByNameSoapResponse">
                <part name="parameters" element="tns:ListOfContinentsByNameResponse"/>
            </message>
        Then our response file name should be `listOfContinentsByNameResponse`
- Appropriate response file names will be written to the file  `responseFileNames.txt`.

# Limitations
- The spring project uses soap1.1
    - Soap1.2 is not provided.
- Since Windows file system forbids the usage of **`/ , \ , : , * , ? , % , " , < , > , |`**
    in name of the files, there cannot be any response file named as such, hence the message elements cannot contain any of these characters.
