from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.http import Http404
from django.template import loader
from django.http.response import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from emgraph.modules import create_graph
from .forms import CategoriesForm
import json
import os
from mizar_graph.settings import GRAPH_DIR

CATEGORIES = ['constructors', 'notations', 'registrations', 'theorems', 'schemes',
              'definitions', 'requirements', 'expansions', 'equalities']

def emgraph(request):
    graph_elements = create_graph.create_graph(CATEGORIES, layout='layered')
    with open(GRAPH_DIR + '/layered_theorem_graph.json', 'r') as f_in:
        graph_elements = json.load(f_in)
    context = {"graph_elements": graph_elements, 'categories': CATEGORIES}
    # return render(request, "mizar_graph_app/emgraph.html", context)
    return render(request, "emgraph/emgraph.html", context)
