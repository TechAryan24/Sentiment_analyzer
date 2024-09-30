from django.contrib import admin
from django.urls import path, include
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('my_app.urls')),
    path('login/',include('my_app.urls')),
    path('signup/',include('my_app.urls')),
    path('result/',include('my_app.urls'))
] 
