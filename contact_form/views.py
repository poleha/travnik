from contact_form.forms import ContactFormModel
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render



def add(request):
    form = ContactFormModel(request.POST, user=request.user)

    if form.is_valid():
        contact_form = form.save()
        return HttpResponse('Данные отправлены!')
    else:
        return render(request, 'contact_form/form.html', {'form': form, 'no_scripts': True})

    #return HttpResponseRedirect(request.POST['back_url'])



