from django.urls import path
from .views import enviar_mensaje, recuperar_mensajes
from .views import download_pdf
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('enviar_mensaje/', enviar_mensaje, name='enviar_mensaje'),
    path('recuperar_mensajes/', recuperar_mensajes, name='recuperar_mensajes'),
    path('download-pdf/<int:objeto_id>/', download_pdf, name='download-pdf')
]
