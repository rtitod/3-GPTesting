import copy
import os
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
import re
import html

from django.views.decorators.csrf import csrf_exempt
from .api import modelo,apikey
from .models import Mensaje, Linea_Comando, Registro_IP

openai.api_key = apikey
chat_context_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting."}
            ]
scan_context_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a interpretar el texto que te pase"}
            ]
add_context_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a interpretar el texto que te pase."}
            ]
result_context_summary_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a sintetizar este texto."}
            ]
result_context_mix_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Quiero que sintetizes estas 3 o menos informaciones de pentesting. sin omitir ninguna y en diferentes parrafos"}
            ]
result_context_other_original = [{"role": "system",
               "content": "Tu eres un asistente experto en seguridad informática y pentesting. Vas a interpretar cada texto que te pase"}
            ]

chat_context = copy.deepcopy(chat_context_original)
scan_context = copy.deepcopy(scan_context_original)
add_context = copy.deepcopy(add_context_original)
result_context_summary = copy.deepcopy(result_context_summary_original)
result_context_mix = copy.deepcopy(result_context_mix_original)
result_context_other = copy.deepcopy(result_context_other_original)

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
                    response_content = html.escape(response_content)
                elif comando[0] == "\\del_cmd":
                    response_content = del_cmd(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\edit_cmd":
                    response_content = edit_cmd(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\list_cmd":
                    response_content = list_cmd(comando)
                elif comando[0] == "\\scan":
                    response_content = scan(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\list":
                    response_content = list(comando)
                elif comando[0] == "\\add":
                    response_content = add(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\print":
                    response_content = print_(comando)
                elif comando[0] == "\\name":
                    response_content = name(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\company":
                    response_content = company(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\result":
                    response_content = result(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\clear":
                    response_content = clear(comando)
                    response_content = html.escape(response_content)
                elif comando[0] == "\\help":
                    response_content = help(comando)
                else:
                    response_content = "Comando no reconocido"
            else:
                print("generando respuesta para chat")
                response_content = get_model_response(chat_context, contenido, )
                if isinstance(response_content, dict) and "error" in response_content:
                    if 'However, your messages resulted in' in response_content['error'] or 'Request too large' in response_content['error']:
                        chat_context.clear()
                        chat_context.extend(copy.deepcopy(chat_context_original))
                    contenido = html.escape(contenido).replace('\n', '<br>')
                    response_content = str(response_content).replace('\n', '<br>')
                    mensaje = Mensaje.objects.create(contenido=contenido,respuesta=response_content)
                    return JsonResponse({'mensaje': mensaje.contenido, 
                                        'respuesta': mensaje.respuesta, 
                                        'fecha': mensaje.fecha.strftime('%Y-%m-%d %H:%M:%S')})
            contenido = html.escape(contenido).replace('\n', '<br>')
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
    try:
        with open("frontend/templates/frontend/tutorial.txt", "r") as file:
            context = {
                    'tutorial': file.read()
                }
    except FileNotFoundError:
        context = {
                    'tutorial': "El archivo de ayuda no se encontró."
                }
    except Exception as e:
        context = {
                    'tutorial': "Ocurrió un error inesperado: " + str(e)
                }
    return render(request, 'frontend/index.html', context)
    
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
        directorio_personalizado = "frontend/scripts"
        comando_personalizado = os.path.join(directorio_personalizado, comando_str)
        if os.path.exists(comando_personalizado.split()[0]) and os.access(comando_personalizado.split()[0], os.X_OK):
            comando = comando_personalizado.split()
            resultado_personalizado = subprocess.check_output(comando, stderr=subprocess.STDOUT, text=True)
            return resultado_personalizado
        else:
            comando = comando_str.split()
            resultado = subprocess.check_output(comando, stderr=subprocess.STDOUT, text=True)
            return resultado
    except subprocess.CalledProcessError as e:
        return f"El comando no existe o se produjo un error: \n {e.output}"
    except Exception as e:
        return f"Ocurrió un error inesperado: \n {str(e)}"

def get_model_response(conversation, user_message, max_attempts=8):
    #user_message = truncate_to_1000_words(user_message)
    conversation.append({"role": "user", "content": user_message})
    for attempt in range(1, max_attempts + 1):
        try:
            response = openai.ChatCompletion.create(
                model=modelo,
                messages=conversation,
                request_timeout=80,
            )
            response_from_api = response['choices'][0]['message']['content']
            conversation.append({"role": "system", "content": response_from_api})
            return response_from_api
        except Exception as e:
            if 'However, your messages resulted in' in str(e) :
                return {"error": "Ocurrió un error inesperado: " + str(e)}
            elif 'Request too large' in str(e) :
                return {"error": "Ocurrió un error inesperado: " + str(e)}
            elif 'Incorrect API key provided' in str(e) :
                return {"error": "Ocurrió un error inesperado: " + str(e)}
            elif attempt == max_attempts:
                return {"error": f"Ocurrió un error inesperado después de {max_attempts} intentos: {str(e)}"}
            else:
                time.sleep(10)

def truncate_to_1000_words(input_string):
    words = input_string.split()
    truncated_words = words[:1000]
    truncated_string = ' '.join(truncated_words)
    return truncated_string

def add_cmd(comando):
    if len(comando) >= 3:
        try:
            existeip = False
            for i in range(2, len(comando)):
                if "$ip" in comando[i]:
                    existeip = True
            if existeip:
                comando[2] = ' '.join(comando[2:])
                Linea_Comando.objects.create(comando=comando[1],parametros=comando[2])
                response_content = "Comando añadido correctamente"
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
            objeto = Linea_Comando.objects.get(id=comando[1])
        except Linea_Comando.DoesNotExist:
            response_content = "No existe una linea de comandos con el id " + str(comando[1]) + " para eliminar"
        except ValueError:
            response_content = "No existe una linea de comandos con el id " + str(comando[1]) + " para eliminar"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            objeto.delete()
            response_content = "Comando borrado correctamente"
    else:
        response_content = "Uso: \\del_cmd id"
    return response_content

def edit_cmd(comando):
    if len(comando) >= 4:
        try:
            existeip = False
            for i in range(3, len(comando)):
                if "$ip" in comando[i]:
                    existeip = True
            if existeip:
                try:
                    objeto = Linea_Comando.objects.get(id=comando[1])
                except Linea_Comando.DoesNotExist:
                    response_content = "No existe una linea de comandos con el id " + str(comando[1]) + " para editar"
                except ValueError:
                    response_content = "No existe una linea de comandos con el id " + str(comando[1]) + " para editar"
                except Exception as e:
                    response_content = "Ocurrió un error inesperado: " +str(e)
                else:
                    comando[3] = ' '.join(comando[3:])
                    setattr(objeto, "comando", comando[2])
                    setattr(objeto, "parametros", comando[3])
                    objeto.save()
                    response_content = "Comando editado correctamente"
            else:
                response_content = "No existe el parámetro $ip"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\edit_cmd id nombre_del_comando (parametros incluyendo $ip)"
    return response_content

def list_cmd(comando):
    if len(comando) == 1:
        try:
            objetos_linea_comando = Linea_Comando.objects.all()
            if objetos_linea_comando.exists():
                tabla_html = "<table class=\"table_commands\">"
                tabla_html += "<tr><th>Id</th><th>Comando</th><th>Parámetros</th></tr>"

                for objeto in objetos_linea_comando:
                    obj_id = objeto.id
                    obj_comando = html.escape(objeto.comando)
                    obj_parametros = html.escape(objeto.parametros)
                    tabla_html += f"<tr><td>{obj_id}</td><td>{obj_comando}</td><td>{obj_parametros}</td></tr>"
                tabla_html += "</table>"
                response_content = tabla_html
            else:
                response_content = "No existen elementos en la tabla lineas de comandos"
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\list_cmd" 
    return response_content

def divide_en_partes(texto, palabras_por_parte=1500):
    palabras = texto.split()
    partes = [palabras[i:i + palabras_por_parte] for i in range(0, len(palabras), palabras_por_parte)]
    return [' '.join(parte) for parte in partes]

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
                        partes_de_la_salida = divide_en_partes(salida)
                        respuesta_completa=""
                        for parte in partes_de_la_salida:
                            scan_context.clear()
                            scan_context.extend(copy.deepcopy(scan_context_original))
                            print("generando respuesta de la salida del comando")
                            respuesta = get_model_response(scan_context, parte)
                            if isinstance(respuesta, dict) and "error" in respuesta:
                                raise MyCustomError(respuesta["error"])
                            respuesta_completa=respuesta_completa + respuesta
                            time.sleep(3)
                        setattr(registro_ip, f"respuesta{i}", respuesta_completa)
                        time.sleep(7)
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
                    obj_host = html.escape(objeto.IP)
                    obj_fecha = objeto.fecha
                    obj_experto = html.escape(objeto.nombre)
                    obj_empresa = html.escape(objeto.empresa)
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
        input_string = ' '.join(comando)
        patron = r'\b\w+\s+\w+\s+\[(.*?)\]\s(.*)'
        coincidencias = re.findall(patron, input_string)
        if coincidencias:
            try:
                objeto = Registro_IP.objects.get(id=comando[1])
            except Registro_IP.DoesNotExist:
                response_content = "No se encontró un objeto con ID " + comando[1]
            except ValueError:
                response_content = "No se encontró un objeto con ID " + comando[1]
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
            else:
                try:
                    contenedor_atributos = [nombre_atributo for nombre_atributo in dir(objeto) if nombre_atributo.startswith("contenedor")]
                    contenedor_atributos_ordenados = sorted(contenedor_atributos, key=lambda x: int(x.lstrip("contenedor")))
                    contenedor_vacio_encontrado = False
                    for atributo in contenedor_atributos_ordenados:
                        if not getattr(objeto, atributo):
                            salida = "[" + coincidencias[0][0] + "]" + ":\n" + coincidencias[0][1]
                            setattr(objeto, atributo, salida)
                            partes_de_la_salida = divide_en_partes(salida)
                            respuesta_completa=""
                            for parte in partes_de_la_salida:
                                add_context.clear()
                                add_context.extend(copy.deepcopy(add_context_original))
                                print("generando respuesta de la entrada personalizada")
                                respuesta = get_model_response(add_context, parte)
                                if isinstance(respuesta, dict) and "error" in respuesta:
                                    raise MyCustomError(respuesta["error"])
                                respuesta_completa=respuesta_completa + '\n' + respuesta
                            numero = atributo.lstrip("contenedor")
                            setattr(objeto, "respuesta" + numero, respuesta_completa)
                            objeto.save()
                            response_content = "La información ha sido añadida correctamente"
                            contenedor_vacio_encontrado = True
                            break
                    if not contenedor_vacio_encontrado:
                        response_content = "No se encontró algún contenedor de información vacío"
                except Exception as e:
                    response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            response_content = "El parametro \"linea de comandos\" no cumple con estar delimitado por: [ ] o no existe el (segundo parametro)" 
    else:
        response_content = "Uso: \\add id_del_scaneo (commando entre []) (texto propio de salida de comando de otra herramienta o informacion propia)" 
    return response_content

def print_(comando):
    if len(comando) == 2:
        try:
            objeto_for_printing = Registro_IP.objects.get(id=comando[1])
        except Registro_IP.DoesNotExist:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
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
                        #correccion simple
                        if texto_a_almacenar.startswith('\n'):
                            texto_a_almacenar = texto_a_almacenar[1:]
                        lineas = html.escape(texto_a_almacenar).split("\n")
                        if lineas:
                            lineas[0] = "<u><b>" + lineas[0] + "</b></u><br>"
                        texto_a_almacenar = "\n".join(lineas)
                        texto_a_almacenar = texto_a_almacenar.replace("\n", "<br>")
                        contenido_contenedores.append(texto_a_almacenar)

                for elemento in respuesta_printing_atributos_ordenados:
                    if getattr(objeto_for_printing, elemento):
                        texto_a_almacenar = getattr(objeto_for_printing, elemento)
                        #correccion simple
                        if texto_a_almacenar.startswith('\n'):
                            texto_a_almacenar = texto_a_almacenar[1:]
                        lineas = html.escape(texto_a_almacenar).split("\n")
                        if lineas:
                            lineas[0] = "<b>" + lineas[0] + "</b>"
                        texto_a_almacenar = "\n".join(lineas)
                        texto_a_almacenar = texto_a_almacenar.replace("\n", "<br>")
                        contenido_respuestas.append(texto_a_almacenar)
                
                contenedores_y_respuestas = zip(contenido_contenedores, contenido_respuestas)
                #permite imprimir sin resultados
                if objeto_for_printing.resumen is None:
                    objeto_for_printing.resumen = " "
                if objeto_for_printing.resultado is None:
                    objeto_for_printing.resultado = " "
                if objeto_for_printing.recomendaciones is None:
                    objeto_for_printing.recomendaciones = " "

                context = {
                    'nombre': html.escape(objeto_for_printing.nombre),
                    'empresa': html.escape(objeto_for_printing.empresa),
                    'resumen': html.escape(objeto_for_printing.resumen).replace("\n", "<br>"),
                    'resultado': html.escape(objeto_for_printing.resultado).replace("\n", "<br>"),
                    'recomendaciones': html.escape(objeto_for_printing.recomendaciones).replace("\n", "<br>"),
                    'contenedores_y_respuestas': contenedores_y_respuestas,
                }
                pdf = render_to_pdf('frontend/get_report_template.html', context)
                pdf_filename = str(objeto_for_printing.id) + "_" + objeto_for_printing.IP + ".pdf"
                pdf_path = "frontend/reports/" + pdf_filename
                with open(pdf_path, 'wb') as pdf_file:
                    pdf_file.write(pdf)
                objeto_for_printing.reporte = pdf_path
                objeto_for_printing.save()
                response_content = "Se generó el documento."
                response_content = response_content + "\n"
                response_content = response_content + "Descárguelo aquí: <a href= \"download-pdf/" + str(comando[1]) + "/\">Descargar reporte</a>\n"
            except PermissionError as e:
                response_content = "Error: Permiso denegado al guardar el PDF: " + str(e)
            except OSError as e:
                response_content = "Error de E/S al guardar el PDF: " + str(e)
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
            objeto = Registro_IP.objects.get(id=comando[1])
        except Registro_IP.DoesNotExist:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                comando[2] = ' '.join(comando[2:])
                objeto.nombre = comando[2]
                objeto.save()
                response_content = "El campo 'nombre' del objeto con ID " + str(comando[1]) + " ha sido modificado a " + comando[2]
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\name id_del_scaneo (Nombre del experto)"   
    return response_content
                
def company(comando):
    if len(comando) >= 3:
        try:
            objeto = Registro_IP.objects.get(id=comando[1])
        except Registro_IP.DoesNotExist:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                comando[2] = ' '.join(comando[2:])
                objeto.empresa = comando[2]
                objeto.save()
                response_content = "El campo 'empresa' del objeto con ID " + str(comando[1]) + " ha sido modificado a " + comando[2]
            except Exception as e:
                response_content = "Ocurrió un error inesperado: " +str(e)
    else:
        response_content = "Uso: \\company id_del_scaneo (Nombre de la empresa a escanear)"   
    return response_content

def result(comando):
    if len(comando) == 2:
        try:
            objeto = Registro_IP.objects.get(id=comando[1])
        except Registro_IP.DoesNotExist:
            response_content = "No se encontró un objeto con ID " + str(comando[1])
        except ValueError:
            response_content = "No se encontró un objeto con ID " + comando[1]
        except Exception as e:
            response_content = "Ocurrió un error inesperado: " +str(e)
        else:
            try:
                respuesta_atributos = [nombre_atributo for nombre_atributo in dir(objeto) if nombre_atributo.startswith("respuesta")]
                respuesta_atributos_ordenados = sorted(respuesta_atributos, key=lambda x: int(x.lstrip("respuesta")))
                existe_contenedor_lleno = False
                result_context_summary.clear()
                result_context_summary.extend(copy.deepcopy(result_context_summary_original))
                respuesta_fragmento=""
                respuesta_parcial=""
                respuesta_completa=""
                counter=0
                for atributo in respuesta_atributos_ordenados:
                    if getattr(objeto, atributo):
                        respuesta=get_model_response(result_context_summary, getattr(objeto, atributo))
                        if isinstance(respuesta, dict) and "error" in respuesta:
                            raise MyCustomError(respuesta["error"])
                        counter = counter + 1
                        respuesta_fragmento=respuesta_fragmento + '\n' + respuesta
                        if counter == 3:
                            time.sleep(10)
                            result_context_mix.clear()
                            result_context_mix.extend(copy.deepcopy(result_context_mix_original))
                            print("procesando fragmento de 3 respuestas")
                            respuesta_parcial=get_model_response(result_context_mix, respuesta_fragmento)
                            if isinstance(respuesta_parcial, dict) and "error" in respuesta_parcial:
                                raise MyCustomError(respuesta_parcial["error"])
                            respuesta_completa=respuesta_completa + '\n' + respuesta_parcial
                            result_context_summary.clear()
                            result_context_summary.extend(copy.deepcopy(result_context_summary_original))
                            respuesta_fragmento=""
                            counter = 0
                        time.sleep(10)
                        existe_contenedor_lleno = True
                if existe_contenedor_lleno == True:
                    if counter < 3 and counter > 0 :
                        result_context_mix.clear()
                        result_context_mix.extend(copy.deepcopy(result_context_mix_original))
                        print("aun hay material. Fragmento de 2 o menos")
                        respuesta_parcial=get_model_response(result_context_mix, respuesta_fragmento)
                        if isinstance(respuesta_parcial, dict) and "error" in respuesta_parcial:
                            raise MyCustomError(respuesta_parcial["error"])
                        respuesta_completa=respuesta_completa + '\n' + respuesta_parcial
                    result_context_other.clear()
                    result_context_other.extend(copy.deepcopy(result_context_other_original))
                    print("generando resultado general")
                    resultado = get_model_response(result_context_other, "Cuál es tu interpretación como experto de este texto? : " + respuesta_completa)
                    if isinstance(resultado, dict) and "error" in resultado:
                        raise MyCustomError(resultado["error"])
                    setattr(objeto, "resultado", resultado)
                    time.sleep(10)
                    result_context_other.clear()
                    result_context_other.extend(copy.deepcopy(result_context_other_original))
                    print("generando resumen")
                    resumen = get_model_response(result_context_other, "resume este texto en menos de 300 letras : " + resultado)
                    if isinstance(resumen, dict) and "error" in resumen:
                            raise MyCustomError(resumen["error"])
                    setattr(objeto, "resumen", resumen)
                    time.sleep(10)
                    result_context_other.clear()
                    result_context_other.extend(copy.deepcopy(result_context_other_original))
                    print("generando recomendaciones")
                    recomendaciones = get_model_response(result_context_other, "dame recomendaciones de seguridad informática en base a esto : " + respuesta_completa)
                    if isinstance(recomendaciones, dict) and "error" in recomendaciones:
                            raise MyCustomError(recomendaciones["error"])
                    setattr(objeto, "recomendaciones", recomendaciones)
                    time.sleep(10)
                    objeto.save()
                    response_content = "Se analizaron las respuestas y se guardaron el resultado, el resumen y las recomendaciones."
                else:
                    response_content = "Todos los contenedores están vacíos"
            except Exception as e:
                response_content = "Ocurrió un error inesperado en result: " +str(e)
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
    pdf = pisa.pisaDocument(BytesIO(html.encode('ISO-8859-1','replace')), result)
    #pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

class MyCustomError(Exception):
    def __init__(self, message):
        super().__init__(message)
