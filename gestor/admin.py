from django.contrib import admin
from .models import Curso, Leccion


class LeccionInline(admin.TabularInline):
    model = Leccion
    extra = 0


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'nivel', 'fecha_creacion')
    inlines = [LeccionInline]


@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'estado', 'duracion')