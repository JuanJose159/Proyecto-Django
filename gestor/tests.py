import shutil
import tempfile
from io import BytesIO

from django.contrib.auth.models import Group, Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Curso

MEDIA_TMP = tempfile.mkdtemp()


def crear_curso(**kw):
    datos = dict(nombre='Python', nivel='basico', descripcion='Intro', duracion=10)
    datos.update(kw)
    return Curso.objects.create(**datos)


def usuario_con_permisos(username, *codenames):
    user = User.objects.create_user(username, password='x')
    grupo = Group.objects.create(name=f'g-{username}')
    grupo.permissions.set(Permission.objects.filter(codename__in=codenames, content_type__app_label='gestor'))
    grupo.user_set.add(user)
    return user


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class CursosTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TMP, ignore_errors=True)
        super().tearDownClass()

    # ---- lectura pública
    def test_lista_publica_y_ruta_principal(self):
        crear_curso(nombre='Django')
        for url in ('/', reverse('cursos')):
            r = self.client.get(url)
            self.assertContains(r, 'Django')

    def test_lista_vacia_muestra_mensaje(self):
        r = self.client.get('/')
        self.assertContains(r, 'No hay cursos disponibles en este momento')

    def test_detalle_publico_y_404(self):
        c = crear_curso()
        self.assertEqual(self.client.get(reverse('curso_detalle', args=[c.id])).status_code, 200)
        self.assertEqual(self.client.get('/cursos/999/').status_code, 404)

    # ---- permisos
    def test_anonimo_es_enviado_a_login(self):
        c = crear_curso()
        for url in (reverse('nuevo_curso'), reverse('editar_curso', args=[c.id])):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertIn('/login/', r.url)

    def test_usuario_sin_permiso_recibe_403(self):
        c = crear_curso()
        self.client.force_login(User.objects.create_user('u', password='x'))
        self.assertEqual(self.client.get(reverse('nuevo_curso')).status_code, 403)
        self.assertEqual(self.client.get(reverse('editar_curso', args=[c.id])).status_code, 403)
        self.assertEqual(self.client.post(reverse('eliminar_curso', args=[c.id])).status_code, 403)
        self.assertTrue(Curso.objects.filter(id=c.id).exists())

    def test_botones_ocultos_sin_permiso(self):
        c = crear_curso()
        self.client.force_login(User.objects.create_user('u', password='x'))
        r = self.client.get('/')
        self.assertNotContains(r, reverse('nuevo_curso'))
        self.assertNotContains(r, reverse('editar_curso', args=[c.id]))

    def test_permiso_se_hereda_del_grupo(self):
        self.client.force_login(usuario_con_permisos('inst', 'add_curso'))
        self.assertEqual(self.client.get(reverse('nuevo_curso')).status_code, 200)
        c = crear_curso()
        self.assertEqual(self.client.get(reverse('editar_curso', args=[c.id])).status_code, 403)

    # ---- crear
    def test_crear_curso(self):
        self.client.force_login(usuario_con_permisos('inst', 'add_curso'))
        r = self.client.post(reverse('nuevo_curso'), {
            'nombre': 'Django', 'descripcion': 'Web', 'duracion': 20, 'nivel': 'intermedio'})
        self.assertRedirects(r, reverse('cursos'))
        c = Curso.objects.get()
        self.assertEqual((c.nombre, c.nivel, c.duracion), ('Django', 'intermedio', 20))
        self.assertEqual(c.imagen.name, 'cursos/logo.jpg')  # imagen por defecto

    def test_crear_con_titulo_vacio_muestra_error(self):
        self.client.force_login(usuario_con_permisos('inst', 'add_curso'))
        r = self.client.post(reverse('nuevo_curso'), {
            'nombre': '', 'descripcion': 'Web', 'duracion': 20, 'nivel': 'basico'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Este campo es obligatorio.')
        self.assertEqual(Curso.objects.count(), 0)

    def test_crear_nivel_invalido_o_duracion_cero(self):
        self.client.force_login(usuario_con_permisos('inst', 'add_curso'))
        r = self.client.post(reverse('nuevo_curso'), {
            'nombre': 'X', 'descripcion': 'Y', 'duracion': 0, 'nivel': 'experto'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Curso.objects.count(), 0)

    def test_crear_con_imagen_valida_e_invalida(self):
        self.client.force_login(usuario_con_permisos('inst', 'add_curso'))
        buf = BytesIO(); Image.new('RGB', (4, 4)).save(buf, 'PNG')
        base = {'nombre': 'Img', 'descripcion': 'Y', 'duracion': 5, 'nivel': 'basico'}
        ok = SimpleUploadedFile('a.png', buf.getvalue(), 'image/png')
        self.client.post(reverse('nuevo_curso'), {**base, 'imagen': ok})
        self.assertTrue(Curso.objects.get().imagen.name.startswith('cursos/a'))
        Curso.objects.all().delete()
        mala = SimpleUploadedFile('a.png', b'no soy una imagen', 'image/png')
        r = self.client.post(reverse('nuevo_curso'), {**base, 'imagen': mala})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Curso.objects.count(), 0)

    # ---- editar
    def test_editar_curso(self):
        c = crear_curso()
        self.client.force_login(usuario_con_permisos('inst', 'change_curso'))
        self.assertContains(self.client.get(reverse('editar_curso', args=[c.id])), 'Python')
        r = self.client.post(reverse('editar_curso', args=[c.id]), {
            'nombre': 'Python 2', 'descripcion': 'Nueva', 'duracion': 30, 'nivel': 'avanzado'})
        self.assertRedirects(r, reverse('curso_detalle', args=[c.id]))
        c.refresh_from_db()
        self.assertEqual((c.nombre, c.nivel, c.duracion), ('Python 2', 'avanzado', 30))
        self.assertEqual(c.imagen.name, 'cursos/logo.jpg')  # sin imagen nueva se conserva

    def test_editar_con_nombre_vacio_no_modifica(self):
        c = crear_curso()
        self.client.force_login(usuario_con_permisos('inst', 'change_curso'))
        r = self.client.post(reverse('editar_curso', args=[c.id]), {
            'nombre': '', 'descripcion': 'X', 'duracion': 3, 'nivel': 'basico'})
        self.assertContains(r, 'Este campo es obligatorio.')
        c.refresh_from_db()
        self.assertEqual(c.nombre, 'Python')

    def test_editar_curso_antiguo_sin_nivel(self):
        c = crear_curso(nivel='')  # como el curso que ya existía en la BD
        self.client.force_login(usuario_con_permisos('inst', 'change_curso'))
        self.assertEqual(self.client.get(reverse('editar_curso', args=[c.id])).status_code, 200)

    # ---- eliminar
    def test_eliminar_solo_por_post_con_permiso(self):
        c = crear_curso()
        self.client.force_login(usuario_con_permisos('inst', 'delete_curso'))
        self.assertEqual(self.client.get(reverse('eliminar_curso', args=[c.id])).status_code, 405)
        self.assertTrue(Curso.objects.filter(id=c.id).exists())
        r = self.client.post(reverse('eliminar_curso', args=[c.id]))
        self.assertRedirects(r, reverse('cursos'))
        self.assertFalse(Curso.objects.filter(id=c.id).exists())

    def test_superusuario_puede_todo(self):
        c = crear_curso()
        self.client.force_login(User.objects.create_superuser('root', password='x'))
        self.assertEqual(self.client.get(reverse('nuevo_curso')).status_code, 200)
        self.assertEqual(self.client.get(reverse('editar_curso', args=[c.id])).status_code, 200)

    def test_navegacion_segun_sesion(self):
        r = self.client.get('/')
        self.assertContains(r, 'Iniciar sesión'); self.assertNotContains(r, 'Salir')
        self.client.force_login(User.objects.create_user('u', password='x'))
        r = self.client.get('/')
        self.assertContains(r, 'Salir'); self.assertNotContains(r, reverse('grupos'))
        self.client.force_login(User.objects.create_user('s', password='x', is_staff=True))
        self.assertContains(self.client.get('/'), reverse('grupos'))
