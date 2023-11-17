# 3-GPTesting
3-GPTesting es una herramienta que pretende usar Modelos Largos de Lenguaje para automatizar la creación de reportes relacionados al pentesting. Esta herramienta facilitaría a los expertos en seguridad la interacción con los sistemas a analizar, evaluando vulnerabilidades y accediendo a información crítica relacionada con posibles puntos de entrada y debilidades en la seguridad.

El módulo de usuario consta de dos partes claramente diferenciadas:

Una de ellas es el submódulo de chat directo con la inteligencia artificial, que permite al usuario obtener asistencia de un asistente de IA configurado para desempeñar el papel de experto en seguridad informática y pentesting.

La otra parte contiene comandos que permiten realizar el escaneo de una dirección específica, controlar las aplicaciones utilizadas y generar reportes, incluyendo la creación de un archivo PDF que contendrá el informe sobre el pentesting realizado.

Este proyecto se ha realizado para la tesis propuesta para el curso de seminario de Tesis 2 llamada Implementación y Evaluación de Una herramienta Automatizada de Pentesting Basado en
LLM.

# Uso
Para poder instalar esta herramienta, se recomienda el uso de Ubuntu a partir de la versión 20.02.
En primer lugar se deberá instalar los siguientes utilitarios:

`sudo apt install git`

`sudo apt install python3`

`sudo apt install python3-pip`

`sudo apt install python3-virtualenv python3-venv`

Para tener una lista de herramientas básicas para el scaneo, tanto automático como manual, se sugiere instalar estas herramientas tambien (se recomienda la instalacion prioritaria de las tres primeras herramientas de la siguiente lista, ya que serán manejadas automáticamente por 3GPTesting, mientras que deberá recoger la salida de las otras herramientas y añadirlas al informe usando el comando \add):

`sudo apt install nmap`

`sudo apt install snmp`

`sudo apt install nikto`

`snap install metasploit-framework`

`sudo apt install sqlmap`

`sudo apt install hydra`

Luego de eso deberá crear un entorno virtual así:

`virtualenv -p python3 3GPTesting`

Después se cambiará de directorio

`cd 3GPTesting`

Luego clonará este repositorio. Como es privado, le pedirá usuario y su token de autorización:

`git clone https://github.com/rtitod/3-GPTesting`

Una vez que tenga el repositorio clonado deberá editar el archivo frontend/api.py y colocar la api key donde corresponda. Como esta es una investigación usando gpt3.5 turbo, se ruega no cambiar el modelo.

La key se le proporcionará si hace una solicitud mediante correo al autor de este programa.

Luego deberá activar el entorno virtual con el siguiente comando:

`source bin/activate`

Lo siguiente que se debe hacer es cambiar de directorio

`cd 3-GPTesting`

Instalar las dependencias

`pip3 install -r requirements.txt`

Y ejecutar la aplicación:

`python3 manage.py runserver`

Luego de esto, dirijase en un navegador web a http://127.0.0.1:8000 y comienze a usar la herramienta.

# Ayuda

Escriba en la interface \help para poder obtener una descripción detallada de todas las opciones que posee esta herramienta.

El procesamiento de la información mediante la API de openai es a veces lento, por lo que deberá esperar hasta 10 minutos para la generación de respuestas e informes.









