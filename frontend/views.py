from django.db import IntegrityError
from django.shortcuts import render
from django.http import JsonResponse
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from wsgiref.util import FileWrapper
import openai
import socket
import subprocess
import time

from django.views.decorators.csrf import csrf_exempt

from .models import Mensaje, Linea_Comando, Registro_IP

openai.api_key = "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"
messages = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting."},
            {"role": "user", "content": "¿Cuál es tu nombre?"}
            ]
messages_report_expert = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a interpretar cada fragmento de texto que te pase"},
            {"role": "user", "content": "¿Cuál es tu nombre?"}
            ]
messages_report_expert_detailed = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a interpretar de forma detallada cada texto que te pase"},
            {"role": "user", "content": "¿Cuál es tu nombre?"}
            ]
modelo = "gpt-3.5-turbo"
#modelo = "gpt-4"
nombre_defecto="3GPTesting"
empresa_defecto="ACME"

def enviar_mensaje(request):
    try:
        if request.method == 'POST':
            contenido = request.POST.get('contenido')
            #is a command?
            firstchar = contenido[0]
            if firstchar == "\\":
                comando = contenido.split()
                if comando[0] == "\\add_cmd":
                    response_content = add_cmd(comando)
                elif comando[0] == "\\del_cmd":
                    response_content = del_cmd(comando)
                elif comando[0] == "\\edit_cmd":
                    response_content = edit_cmd(comando)
                elif comando[0] == "\\list_cmd":
                    response_content = list_cmd(comando)
                elif comando[0] == "\\scan":
                    response_content = scan(comando)
                elif comando[0] == "\\list":
                    response_content = list(comando)
                elif comando[0] == "\\add":
                    response_content = add(comando)
                elif comando[0] == "\\print":
                    response_content = print(comando)
                elif comando[0] == "\\name":
                    response_content = name(comando)
                elif comando[0] == "\\company":
                    response_content = company(comando)
                elif comando[0] == "\\result":
                    response_content = result(comando)
                elif comando[0] == "\\clear":
                    response_content = clear(comando)
                elif comando[0] == "\\help":
                    response_content = help(comando)
                else:
                    response_content = "Comando no reconocido"
            else:
                messages[-1]["content"] = contenido
                response_content = get_model_response(messages, contenido)
            contenido = contenido.replace('\n', '<br>')
            response_content = response_content.replace('\n', '<br>')
            mensaje = Mensaje.objects.create(contenido=contenido,respuesta=response_content)
            return JsonResponse({'mensaje': mensaje.contenido, 
                                'respuesta': mensaje.respuesta, 
                                'fecha': mensaje.fecha.strftime('%Y-%m-%d %H:%M:%S')})
    except Exception as e:
        return JsonResponse({'error': str(e)})

def recuperar_mensajes(request):
    try:
        mensajes = Mensaje.objects.all()
        data = [{'mensaje': mensaje.contenido,
                'respuesta': mensaje.respuesta,
                'fecha': mensaje.fecha.strftime('%Y-%m-%d %H:%M:%S')} for mensaje in mensajes]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)})

def index(request):
    return render(request, 'frontend/index.html')

def es_ip_o_host_valido(cadena):
    try:
        socket.inet_aton(cadena)
        return True
    except socket.error:
        try:
            socket.gethostbyname(cadena)
            return True
        except socket.gaierror:
            return False
        
def ejecutar_comando(comando_str):
    try:
        comando = comando_str.split()
        resultado = subprocess.check_output(comando, stderr=subprocess.STDOUT, text=True)
        return resultado
    except subprocess.CalledProcessError as e:
        return f"El comando no existe o se produjo un error: \n {e.output}"
    except Exception as e:
        return f"Ocurrió un error inesperado: \n {str(e)}"

def get_model_response(conversation, user_message):
    try:
        conversation.append({"role": "user", "content": user_message})
        response = openai.ChatCompletion.create(
            model=modelo,
            messages=conversation
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return {"error": "Ocurrió un error inesperado: " + str(e)}

def add_cmd(comando):
    if len(comando) >= 3:
        try:
            existeip = False
            for i in range(2, len(comando)):
                if "$ip" in comando[i]:
                    existeip = True
            if existeip:
                existecomando = Linea_Comando.objects.filter(comando=comando[1])
                if not existecomando:
                    comando[2] = ' '.join(comando[2:])
                    Linea_Comando.objects.create(comando=comando[1],parametros=comando[2])
                    response_content = "Comando añadido correctamente"
                else:
                    response_content = "El comando ya existe en la base de datos"
            else:
                response_content = "No existe el parámetro $ip"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\add_cmd nombre_del_comando (parametros incluyendo $ip)"
    return response_content

def del_cmd(comando):
    if len(comando) == 2:
        try:
            objetos_a_eliminar = Linea_Comando.objects.filter(comando=comando[1])
            if objetos_a_eliminar:
                objetos_a_eliminar.delete()
                response_content = "Comando borrado correctamente"
            else:
                response_content = "No existe ese comando para editar"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\del_cmd nombre_del_comando"
    return response_content

def edit_cmd(comando):
    if len(comando) >= 3:
        try:
            existeip = False
            for i in range(2, len(comando)):
                if "$ip" in comando[i]:
                    existeip = True
            if existeip:
                existecomando = Linea_Comando.objects.filter(comando=comando[1])
                if existecomando:
                    comando[2] = ' '.join(comando[2:])
                    existecomando.delete()
                    Linea_Comando.objects.create(comando=comando[1],parametros=comando[2])
                    response_content = "Comando editado correctamente"
                else:
                    response_content = "El comando no existe en la base de datos"
            else:
                response_content = "No existe el parámetro $ip"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\edit_cmd nombre_del_comando (parametros incluyendo $ip)"
    return response_content

def list_cmd(comando):
    if len(comando) == 1:
        try:
            objetos_linea_comando = Linea_Comando.objects.all()
            if objetos_linea_comando.exists():
                tabla_html = "<table class=\"table_commands\">"
                tabla_html += "<tr><th>Comando</th><th>Parámetros</th></tr>"

                for objeto in objetos_linea_comando:
                    obj_comando = objeto.comando
                    obj_parametros = objeto.parametros
                    tabla_html += f"<tr><td>{obj_comando}</td><td>{obj_parametros}</td></tr>"
                tabla_html += "</table>"
                response_content = tabla_html
            else:
                response_content = "No existen elementos en la tabla lineas de comandos"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\list_cmd" 
    return response_content

def scan(comando):
    if len(comando) == 2:
        try:
            objetos_linea_comando = Linea_Comando.objects.all()
            if objetos_linea_comando.exists():
                if es_ip_o_host_valido(comando[1]):
                    registro_ip = Registro_IP.objects.create(IP=comando[1],empresa=empresa_defecto,nombre=nombre_defecto)
                    for i, objeto in enumerate(objetos_linea_comando, start=1):
                        parametros_modificados = objeto.parametros.replace("$ip", comando[1])
                        linea_de_comando = objeto.comando + ' ' + parametros_modificados
                        salida = ejecutar_comando(linea_de_comando)
                        salida = "[" + linea_de_comando + "]:\n" + salida
                        setattr(registro_ip, f"contenedor{i}", salida)
                        messages_report_expert[-1]["content"] = salida
                        respuesta = get_model_response(messages_report_expert, salida)
                        if "error" in respuesta:
                            raise MyCustomError(respuesta["error"])
                        setattr(registro_ip, f"respuesta{i}", respuesta)
                        time.sleep(2)
                    registro_ip.save()
                    response_content = "El escaneo a la dirección: " + comando[1] + " ha sido completado."
                else:
                    response_content = "La ip o host no es válido al parecer"
            else:
                response_content = "No existen elementos en la tabla"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\scan $IP "
    return response_content

def list(comando):
    if len(comando) == 1:
        try:
            objetos_registro_ip = Registro_IP.objects.all()
            if objetos_registro_ip.exists():
                tabla_html = "<table class=\"table_scans\">"
                tabla_html += "<tr><th>ID</th><th>Host</th><th>Fecha</th><th>Experto</th><th>Empresa</th></tr>"

                for objeto in objetos_registro_ip:
                    obj_id = objeto.id
                    obj_host = objeto.IP
                    obj_fecha = objeto.fecha
                    obj_experto = objeto.nombre
                    obj_empresa = objeto.empresa
                    tabla_html += f"<tr><td>{obj_id}</td><td>{obj_host}</td><td>{obj_fecha}</td><td>{obj_experto}</td><td>{obj_empresa}</td></tr>"
                tabla_html += "</table>"
                response_content = tabla_html
            else:
                response_content = "No existen elementos en la tabla registros"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\list"
    return response_content

def add(comando):
    if len(comando) >= 4:
        if comando[2].startswith("[") and comando[2].endswith("]"):
            try:
                id_a_buscar = int(comando[1]) 
            except ValueError:
                response_content = "No se encontró un objeto con ID " + comando[1]
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
            else:
                try:
                    objeto = Registro_IP.objects.get(id=id_a_buscar)
                except Registro_IP.DoesNotExist:
                    response_content = "No se encontró un objeto con ID " + str(id_a_buscar)
                except Exception as e:
                    response_content = "Ocurrió un error inesperado: " +str(e)
                else:
                    contenedor_atributos = [nombre_atributo for nombre_atributo in dir(objeto) if nombre_atributo.startswith("contenedor")]
                    contenedor_atributos_ordenados = sorted(contenedor_atributos, key=lambda x: int(x.lstrip("contenedor")))
                    contenedor_vacio_encontrado = False
                    for atributo in contenedor_atributos_ordenados:
                        if not getattr(objeto, atributo):
                            comando[3] = ' '.join(comando[3:])
                            salida = comando[2] + ":\n" + comando[3]
                            setattr(objeto, atributo, salida)
                            messages_report_expert[-1]["content"] = salida
                            respuesta = get_model_response(messages_report_expert, salida)
                            if "error" in respuesta:
                                raise MyCustomError(respuesta["error"])
                            numero = atributo.lstrip("contenedor")
                            setattr(objeto, "respuesta" + numero, respuesta)
                            objeto.save()
                            response_content = "La información ha sido añadida correctamente"
                            contenedor_vacio_encontrado = True
                            break
                    if not contenedor_vacio_encontrado:
                        response_content = "No se encontró algún contenedor de información vacío"
        else:
            response_content = "El parametro \"linea de comandos\" no cumple con estar delimitado por: [ ]" 
    else:
        response_content = "Uso: \\add id_del_scaneo commando_entre_[] (texto propio de salida de comando de otra herramienta o informacion propia)" 
    return response_content

def print(comando):
    if len(comando) == 2:
        try:
            id_a_buscar = int(comando[1]) 
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                objeto_for_printing = Registro_IP.objects.get(id=id_a_buscar)
            except Registro_IP.DoesNotExist:
                response_content = "No se encontró un objeto con ID " + str(id_a_buscar)
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
            else:
                try:
                    contenedor_printing_atributos = [nombre_atributo for nombre_atributo in dir(objeto_for_printing) if nombre_atributo.startswith("contenedor")]
                    contenedor_printing_atributos_ordenados = sorted(contenedor_printing_atributos, key=lambda x: int(x.lstrip("contenedor")))

                    respuesta_printing_atributos = [nombre_atributo for nombre_atributo in dir(objeto_for_printing) if nombre_atributo.startswith("respuesta")]
                    respuesta_printing_atributos_ordenados = sorted(respuesta_printing_atributos, key=lambda x: int(x.lstrip("respuesta")))

                    contenido_contenedores = []
                    contenido_respuestas = []

                    for elemento in contenedor_printing_atributos_ordenados:
                        if getattr(objeto_for_printing, elemento):
                            texto_a_almacenar = getattr(objeto_for_printing, elemento)
                            lineas = texto_a_almacenar.split("\n")
                            if lineas:
                                lineas[0] = "<u><b>" + lineas[0] + "</b></u><br>"
                            texto_a_almacenar = "\n".join(lineas)
                            texto_a_almacenar = texto_a_almacenar.replace("\n", "<br>")
                            contenido_contenedores.append(texto_a_almacenar)

                    for elemento in respuesta_printing_atributos_ordenados:
                        if getattr(objeto_for_printing, elemento):
                            texto_a_almacenar = getattr(objeto_for_printing, elemento)
                            lineas = texto_a_almacenar.split("\n")
                            if lineas:
                                lineas[0] = "<b>" + lineas[0] + "</b>"
                            texto_a_almacenar = "\n".join(lineas)
                            texto_a_almacenar = texto_a_almacenar.replace("\n", "<br>")
                            contenido_respuestas.append(texto_a_almacenar)
                    
                    contenedores_y_respuestas = zip(contenido_contenedores, contenido_respuestas)
                    
                    context = {
                        'nombre': objeto_for_printing.nombre,
                        'empresa': objeto_for_printing.empresa,
                        'resumen': objeto_for_printing.resumen.replace("\n", "<br>"),
                        'resultado': objeto_for_printing.resultado.replace("\n", "<br>"),
                        'recomendaciones': objeto_for_printing.recomendaciones.replace("\n", "<br>"),
                        'contenedores_y_respuestas': contenedores_y_respuestas,
                    }
                    pdf = render_to_pdf('frontend/get_report_template.html', context)
                    pdf_filename = str(objeto_for_printing.id) + "_" + objeto_for_printing.IP + ".pdf"
                    pdf_path = "frontend/reports/" + pdf_filename
                    try:
                        with open(pdf_path, 'wb') as pdf_file:
                            pdf_file.write(pdf)
                    except Exception as e:
                        response_content = "Error de E/S al guardar el PDF: " + str(e)
                    objeto_for_printing.reporte = pdf_path
                    objeto_for_printing.save()
                    response_content = "Se generó el documento."
                    response_content = response_content + "\n"
                    response_content = response_content + "Descárguelo aquí: <a href= \"download-pdf/" + str(id_a_buscar) + "/\">Descargar reporte</a>\n"
                except Exception as e:
                    response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\print id_del_scaneo" 
    return response_content

def download_pdf(request, objeto_id):
    try:
        objeto_for_printing = Registro_IP.objects.get(id=objeto_id)
        pdf_path = objeto_for_printing.reporte

        # Abre el archivo PDF en modo de lectura binaria
        with open(pdf_path, 'rb') as pdf_file:
            response = HttpResponse(FileWrapper(pdf_file), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_path}"'
            return response
    except Registro_IP.DoesNotExist:
        response_content = "No se encontró un objeto con ese ID."
    except Exception as e:
        response_content = f"Ocurrió un error inesperado: {str(e)}"

    return HttpResponse(response_content)

def name(comando):
    if len(comando) >= 3:
        try:
            id_a_buscar = int(comando[1])  
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        else:
            try:
                objeto = Registro_IP.objects.get(id=id_a_buscar)
            except Registro_IP.DoesNotExist:
                response_content = "No se encontró un objeto con ID " + str(id_a_buscar)
            else:
                comando[2] = ' '.join(comando[2:])
                objeto.nombre = comando[2]
                objeto.save()
                response_content = "El campo 'nombre' del objeto con ID " + str(id_a_buscar) + " ha sido modificado a " + comando[2]
    else:
        response_content = "Uso: \\name id_del_scaneo (Nombre del experto)"   
    return response_content
                
def company(comando):
    if len(comando) >= 3:
        try:
            id_a_buscar = int(comando[1]) 
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                objeto = Registro_IP.objects.get(id=id_a_buscar)
            except Registro_IP.DoesNotExist:
                response_content = "No se encontró un objeto con ID " + str(id_a_buscar)
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
            else:
                comando[2] = ' '.join(comando[2:])
                objeto.empresa = comando[2]
                objeto.save()
                response_content = "El campo 'empresa' del objeto con ID " + str(id_a_buscar) + " ha sido modificado a " + comando[2]
    else:
        response_content = "Uso: \\company id_del_scaneo (Nombre de la empresa a escanear)"   
    return response_content

def result(comando):
    if len(comando) == 2:
        try:
            id_a_buscar = int(comando[1]) 
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                objeto = Registro_IP.objects.get(id=id_a_buscar)
            except Registro_IP.DoesNotExist:
                response_content = "No se encontró un objeto con ID " + str(id_a_buscar)
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
            else:
                respuesta_atributos = [nombre_atributo for nombre_atributo in dir(objeto) if nombre_atributo.startswith("respuesta")]
                respuesta_atributos_ordenados = sorted(respuesta_atributos, key=lambda x: int(x.lstrip("respuesta")))
                existe_contenedor_lleno = False
                for atributo in respuesta_atributos_ordenados:
                    if getattr(objeto, atributo):
                        messages_report_expert_detailed[-1]["content"] = getattr(objeto, atributo)
                        respuesta=get_model_response(messages_report_expert_detailed, getattr(objeto, atributo))
                        if "error" in respuesta:
                            raise MyCustomError(respuesta["error"])
                        time.sleep(3)
                        existe_contenedor_lleno = True
                if existe_contenedor_lleno == True:
                    messages_report_expert_detailed[-1]["content"] = "Cuál es tu interpretación como experto de todo el texto introducido previamente?"
                    resultado = get_model_response(messages_report_expert_detailed, "Cuál es tu interpretación como experto de todo el texto introducido previamente?")
                    if "error" in resultado:
                            raise MyCustomError(resultado["error"])
                    setattr(objeto, "resultado", resultado)
                    time.sleep(5)
                    messages_report_expert_detailed[-1]["content"] = "resume tu interpretacion en menos de 350 letras"
                    resumen = get_model_response(messages_report_expert_detailed, "resume este texto en menos de 300 letras")
                    if "error" in resumen:
                            raise MyCustomError(resumen["error"])
                    setattr(objeto, "resumen", resumen)
                    time.sleep(5)
                    messages_report_expert_detailed[-1]["content"] = "dame recomendaciones de seguridad informática en base a todo lo que me dijistes"
                    recomendaciones = get_model_response(messages_report_expert_detailed, "dame recomendaciones de seguridad informática en base a todo lo que me dijistes")
                    if "error" in recomendaciones:
                            raise MyCustomError(recomendaciones["error"])
                    setattr(objeto, "recomendaciones", recomendaciones)
                    time.sleep(5)
                    objeto.save()
                    response_content = "Se analizaron las respuestas y se guardaron el resultado, el resumen y las recomendaciones."
                else:
                    response_content = "Todos los contenedores están vacíos"
    else:
        response_content = "Uso: \\result id_del_scaneo" 
    return response_content
    
def clear(comando):
    if len(comando) == 1:
        try:
            response_content = "Limpiando...\n"
            Mensaje.objects.all().delete()
        except IntegrityError as e:
            response_content += "Error al borrar los mensajes: " + str(e)
        except Exception as e:
            response_content += "Ocurrió un error inesperado: " + str(e)
    else:
        response_content = "Uso: \\clear"
    return response_content 

def help(comando):
    if len(comando) == 1:
        try:
            with open("frontend/templates/frontend/commands.txt", "r") as file:
                response_content = file.read()
        except FileNotFoundError:
            response_content = "El archivo de ayuda no se encontró."
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " + str(e)
    else:
        response_content = "Uso: \\help"
    return response_content

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return result.getvalue()
    return None

class MyCustomError(Exception):
    def __init__(self, message):
        super().__init__(message)
