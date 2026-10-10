from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Curso, Leccion
from .forms import CursoForm, LeccionForm


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------
def lista_cursos(request):
    cursos = Curso.objects.annotate(total_lecciones=Count('lecciones')).order_by('-fecha_creacion')
    return render(request, 'cursos.html', {'cursos': cursos})


def detalle_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    lecciones = curso.lecciones.all().order_by('fecha_creacion')
    return render(request, 'detalle_curso.html', {'curso': curso, 'lecciones': lecciones})


@login_required
def crear_curso(request):
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect('lista_cursos')
    else:
        form = CursoForm()
    return render(request, 'curso_form.html', {'form': form})


@login_required
def editar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso actualizado.")
            return redirect('detalle_curso', pk=curso.pk)
    else:
        form = CursoForm(instance=curso)
    return render(request, 'curso_form.html', {'form': form, 'curso': curso})


@login_required
def eliminar_curso(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, "Curso eliminado.")
    return redirect('lista_cursos')


# ---------------------------------------------------------------------------
# Lecciones
# ---------------------------------------------------------------------------
@login_required
def agregar_leccion(request, curso_pk):
    curso = get_object_or_404(Curso, pk=curso_pk)
    if request.method == 'POST':
        form = LeccionForm(request.POST)
        if form.is_valid():
            leccion = form.save(commit=False)
            leccion.curso = curso          # clave foránea al curso actual
            leccion.save()
            messages.success(request, "Lección agregada.")
            return redirect('detalle_curso', pk=curso.pk)
    else:
        form = LeccionForm()
    return render(request, 'leccion_form.html', {'form': form, 'curso': curso, 'accion': 'Agregar'})


@login_required
def editar_leccion(request, pk):
    leccion = get_object_or_404(Leccion, pk=pk)
    curso = leccion.curso
    if request.method == 'POST':
        form = LeccionForm(request.POST, instance=leccion)
        if form.is_valid():
            form.save()
            messages.success(request, "Lección actualizada.")
            return redirect('detalle_curso', pk=curso.pk)
    else:
        form = LeccionForm(instance=leccion)
    return render(request, 'leccion_form.html', {'form': form, 'curso': curso, 'accion': 'Editar'})


@login_required
def eliminar_leccion(request, pk):
    leccion = get_object_or_404(Leccion, pk=pk)
    curso = leccion.curso
    if request.method == 'POST':
        leccion.delete()
        messages.success(request, "Lección eliminada.")
        return redirect('detalle_curso', pk=curso.pk)
    return render(request, 'leccion_confirmar_eliminacion.html', {'leccion': leccion, 'curso': curso})