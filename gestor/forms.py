from django import forms
from .models import Curso, Leccion

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['titulo', 'descripcion', 'nivel', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'Título del curso'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'rows': 4, 'placeholder': 'Descripción'}),
            'nivel': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }

class LeccionForm(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = ['titulo', 'contenido', 'duracion', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'Título de la lección'}),
            'contenido': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'rows': 4, 'placeholder': 'Contenido de la lección'}),
            'duracion': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'Minutos'}),
            'estado': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }