from django.db import models
from django.urls import reverse

class Curso(models.Model):
    NIVEL_CHOICES = [
        ('Principiante', 'Principiante'),
        ('Intermedio', 'Intermedio'),
        ('Avanzado', 'Avanzado'),
    ]
    
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='Principiante')
    imagen = models.ImageField(upload_to='cursos/', blank=True, null=True, verbose_name="Imagen")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('detalle_curso', kwargs={'pk': self.pk})


class Leccion(models.Model):
    ESTADO_CHOICES = [
        ('Borrador', 'Borrador'),
        ('Publicado', 'Publicado'),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='lecciones')
    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(verbose_name="Contenido")
    duracion = models.PositiveIntegerField(help_text="Duración en minutos", verbose_name="Duración (min)")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Borrador')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.curso.titulo}"