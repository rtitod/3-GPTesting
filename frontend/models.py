from django.db import models

# Create your models here.

class Mensaje(models.Model):
    contenido = models.TextField()
    respuesta = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

class Linea_Comando(models.Model):
    comando = models.TextField(blank=False)
    parametros = models.TextField(blank=False)

class Registro_IP(models.Model):
    IP = models.TextField(blank=False)
    fecha = models.DateTimeField(auto_now_add=True,blank=False)
    nombre = models.TextField(null=True, blank=True)
    empresa = models.TextField(null=True, blank=True)
    contenedor1 = models.TextField(null=True, blank=True)
    contenedor2 = models.TextField(null=True, blank=True)
    contenedor3 = models.TextField(null=True, blank=True)
    contenedor4 = models.TextField(null=True, blank=True)
    contenedor5 = models.TextField(null=True, blank=True)
    contenedor6 = models.TextField(null=True, blank=True)
    contenedor7 = models.TextField(null=True, blank=True)
    contenedor8 = models.TextField(null=True, blank=True)
    contenedor9 = models.TextField(null=True, blank=True)
    contenedor10 = models.TextField(null=True, blank=True)
    contenedor11 = models.TextField(null=True, blank=True)
    contenedor12 = models.TextField(null=True, blank=True)
    contenedor13 = models.TextField(null=True, blank=True)
    contenedor14 = models.TextField(null=True, blank=True)
    contenedor15 = models.TextField(null=True, blank=True)
    respuesta1 = models.TextField(null=True, blank=True)
    respuesta2 = models.TextField(null=True, blank=True)
    respuesta3 = models.TextField(null=True, blank=True)
    respuesta4 = models.TextField(null=True, blank=True)
    respuesta5 = models.TextField(null=True, blank=True)
    respuesta6 = models.TextField(null=True, blank=True)
    respuesta7 = models.TextField(null=True, blank=True)
    respuesta8 = models.TextField(null=True, blank=True)
    respuesta9 = models.TextField(null=True, blank=True)
    respuesta10 = models.TextField(null=True, blank=True)
    respuesta11 = models.TextField(null=True, blank=True)
    respuesta12 = models.TextField(null=True, blank=True)
    respuesta13 = models.TextField(null=True, blank=True)
    respuesta14 = models.TextField(null=True, blank=True)
    respuesta15 = models.TextField(null=True, blank=True)
    resultado = models.TextField(null=True, blank=True)
    recomendaciones = models.TextField(null=True, blank=True)
    resumen = models.TextField(null=True, blank=True)
    reporte = models.TextField(null=True, blank=True)
