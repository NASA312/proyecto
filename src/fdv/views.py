from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Count
@login_required(login_url = reverse_lazy('auth:login'))
def index(request):
    return render(request, 'index.html')