from django.urls import path
from . import views

urlpatterns = [
    # Cursos
    path('', views.lista_cursos, name='lista_cursos'),
    path('', views.lista_cursos, name='home'),     # alias usado por base.html / accounts
    path('', views.lista_cursos, name='cursos'),   # alias usado por base.html
    path('curso/nuevo/', views.crear_curso, name='crear_curso'),
    path('curso/nuevo/', views.crear_curso, name='nuevo_curso'),  # alias
    path('curso/<int:pk>/', views.detalle_curso, name='detalle_curso'),
    path('curso/<int:pk>/editar/', views.editar_curso, name='editar_curso'),
    path('curso/<int:pk>/eliminar/', views.eliminar_curso, name='eliminar_curso'),

    # Lecciones
    path('curso/<int:curso_pk>/leccion/nueva/', views.agregar_leccion, name='agregar_leccion'),
    path('leccion/<int:pk>/editar/', views.editar_leccion, name='editar_leccion'),
    path('leccion/<int:pk>/eliminar/', views.eliminar_leccion, name='eliminar_leccion'),
]