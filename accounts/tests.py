from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse


class RegistroLoginTests(TestCase):
    datos = {
        'username': 'ana', 'email': 'ana@correo.com',
        'first_name': 'Ana', 'last_name': 'Gómez',
        'password1': 'Clave-Segura-2026', 'password2': 'Clave-Segura-2026',
    }

    def test_registro_crea_usuario_y_inicia_sesion(self):
        r = self.client.post(reverse('registro'), self.datos)
        self.assertRedirects(r, reverse('home'))
        user = User.objects.get(username='ana')
        self.assertTrue(user.check_password('Clave-Segura-2026'))  # contraseña encriptada
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_registro_contrasenas_distintas(self):
        r = self.client.post(reverse('registro'), {**self.datos, 'password2': 'otra'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Las contraseñas no coinciden.')
        self.assertFalse(User.objects.filter(username='ana').exists())

    def test_registro_contrasena_debil_es_rechazada(self):
        r = self.client.post(reverse('registro'), {**self.datos, 'password1': '1234', 'password2': '1234'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='ana').exists())

    def test_registro_usuario_y_correo_duplicados(self):
        User.objects.create_user('ana', 'ana@correo.com', 'x')
        r = self.client.post(reverse('registro'), self.datos)
        self.assertContains(r, 'El nombre de usuario ya existe.')
        self.assertContains(r, 'El correo electrónico ya está registrado.')

    def test_login_y_logout(self):
        User.objects.create_user('ana', 'ana@correo.com', 'Clave-Segura-2026')
        r = self.client.post(reverse('login'), {'username': 'ana', 'password': 'Clave-Segura-2026'})
        self.assertRedirects(r, reverse('home'))
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_incorrecto_muestra_error(self):
        r = self.client.post(reverse('login'), {'username': 'nadie', 'password': 'mal'})
        self.assertContains(r, 'Usuario o contraseña incorrectos.')


class GruposTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', password='x', is_staff=True)
        self.normal = User.objects.create_user('normal', password='x')
        self.client.force_login(self.admin)

    def test_solo_staff_accede_a_grupos(self):
        self.client.force_login(self.normal)
        for nombre in ('grupos', 'permisos'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn('/login/', r.url)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('grupos')).status_code, 302)

    def test_crear_grupo(self):
        self.client.post(reverse('grupos'), {'nombre_grupo': 'Instructores'})
        self.assertTrue(Group.objects.filter(name='Instructores').exists())

    def test_crear_grupo_duplicado_o_vacio_no_duplica(self):
        Group.objects.create(name='Instructores')
        self.client.post(reverse('grupos'), {'nombre_grupo': 'instructores'})
        self.client.post(reverse('grupos'), {'nombre_grupo': '   '})
        self.assertEqual(Group.objects.count(), 1)

    def test_editar_grupo(self):
        g = Group.objects.create(name='Viejo')
        r = self.client.post(reverse('editar_grupo', args=[g.id]), {'name': 'Nuevo'})
        self.assertRedirects(r, reverse('grupos'))
        g.refresh_from_db()
        self.assertEqual(g.name, 'Nuevo')

    def test_editar_grupo_nombre_vacio_o_repetido_no_rompe(self):
        g = Group.objects.create(name='A')
        Group.objects.create(name='B')
        for nombre in ('', 'B'):
            r = self.client.post(reverse('editar_grupo', args=[g.id]), {'name': nombre})
            self.assertEqual(r.status_code, 302)
        g.refresh_from_db()
        self.assertEqual(g.name, 'A')

    def test_pagina_editar_grupo_renderiza_con_js_corregido(self):
        g = Group.objects.create(name='A')
        r = self.client.get(reverse('editar_grupo', args=[g.id]))
        self.assertContains(r, '`${length} / 150`')

    def test_eliminar_grupo_solo_por_post(self):
        g = Group.objects.create(name='A')
        self.assertEqual(self.client.get(reverse('eliminar_grupo', args=[g.id])).status_code, 405)
        self.assertTrue(Group.objects.filter(id=g.id).exists())
        self.client.post(reverse('eliminar_grupo', args=[g.id]))
        self.assertFalse(Group.objects.filter(id=g.id).exists())

    def test_agregar_y_quitar_usuario_del_grupo(self):
        g = Group.objects.create(name='A')
        self.client.post(reverse('agregar_usuario_grupo', args=[g.id]), {'id_user': self.normal.id})
        self.assertIn(self.normal, g.user_set.all())
        r = self.client.get(reverse('editar_grupo', args=[g.id]))
        self.assertIn(self.normal, r.context['miembros'])
        self.assertNotIn(self.normal, r.context['no_miembros'])
        self.client.post(reverse('eliminar_usuario_grupo', args=[g.id]), {'id_user': self.normal.id})
        self.assertNotIn(self.normal, g.user_set.all())

    def test_asignar_permisos_a_grupo(self):
        g = Group.objects.create(name='A')
        p = Permission.objects.get(codename='add_curso')
        self.client.post(reverse('permisos'), {'grupo': g.id, 'permisos': [p.id]})
        self.assertEqual(list(g.permissions.all()), [p])

    def test_permisos_sin_grupos_no_falla(self):
        self.assertEqual(self.client.get(reverse('permisos')).status_code, 200)
        self.assertEqual(self.client.post(reverse('permisos'), {'permisos': []}).status_code, 200)
