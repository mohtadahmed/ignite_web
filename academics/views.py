from django.shortcuts import render

# Create your views here.
def generic_base(request):
    return render(request, 'generic_base.html')