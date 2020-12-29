from django.urls import path

from . import views

urlpatterns = [
    # ex: /mizar_graph_app/
    path('emgraph/', views.emgraph, name='emgraph'),
]