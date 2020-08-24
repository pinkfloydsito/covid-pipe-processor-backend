from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from entities.models import CovidPipe

class PipeCreate(CreateView):
    model = CovidPipe
    fields = ['name']

class PipeUpdate(UpdateView):
    model = CovidPipe
    fields = ['name']

class PipeDelete(DeleteView):
    model = CovidPipe
    success_url = reverse_lazy('pipe-list')
