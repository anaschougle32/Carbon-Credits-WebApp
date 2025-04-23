from django.shortcuts import render

def register_hub(request):
    """
    View for the registration hub page
    """
    return render(request, 'auth/register.html') 