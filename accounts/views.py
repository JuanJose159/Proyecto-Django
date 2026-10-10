from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST


# ---------------------------------------------------------------------------
# Registro de usuarios (el inicio y cierre de sesión usan LoginView/LogoutView)
# ---------------------------------------------------------------------------
def registro(request):
    datos = {}
    errors = []

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        datos = request.POST

        if not all([username, email, first_name, last_name, password1]):
            errors.append("Todos los campos son obligatorios.")

        if password1 != password2:
            errors.append("Las contraseñas no coinciden.")

        if username and User.objects.filter(username__iexact=username).exists():
            errors.append("El nombre de usuario ya existe.")

        if email and User.objects.filter(email__iexact=email).exists():
            errors.append("El correo electrónico ya está registrado.")

        # Aplica los AUTH_PASSWORD_VALIDATORS de settings.py
        if password1 and password1 == password2:
            try:
                validate_password(password1, user=User(username=username, email=email))
            except ValidationError as e:
                errors.extend(e.messages)

        if not errors:
            # create_user encripta la contraseña
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            return redirect("home")

    return render(request, "registro.html", {"errors": errors, "datos": datos})


# ---------------------------------------------------------------------------
# Grupos (solo personal administrativo: is_staff)
# ---------------------------------------------------------------------------
def es_admin(user):
    # is_staff marca a los usuarios con acceso de administración
    return user.is_authenticated and user.is_staff


@user_passes_test(es_admin)
def grupos(request):
    if request.method == "POST":
        nombre = (request.POST.get('nombre_grupo') or "").strip()
        if not nombre:
            messages.error(request, "El nombre del grupo es obligatorio.")
        elif Group.objects.filter(name__iexact=nombre).exists():
            messages.error(request, f"Ya existe un grupo llamado «{nombre}».")
        else:
            Group.objects.create(name=nombre)
            messages.success(request, f"Grupo «{nombre}» creado.")
        return redirect('grupos')

    return render(request, 'grupos.html', {'grupos': Group.objects.all()})


@user_passes_test(es_admin)
@require_POST
def eliminar_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)
    nombre = grupo.name
    grupo.delete()
    messages.success(request, f"Grupo «{nombre}» eliminado.")
    return redirect('grupos')


def dar_miembros(grupo):
    return grupo.user_set.all()


def dar_no_miembros(grupo):
    return User.objects.exclude(id__in=dar_miembros(grupo).values_list('id', flat=True))


@user_passes_test(es_admin)
def editar_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)

    if request.method == "POST":
        nuevo_nombre = (request.POST.get('name') or "").strip()
        if not nuevo_nombre:
            messages.error(request, "El nombre del grupo es obligatorio.")
        elif Group.objects.filter(name__iexact=nuevo_nombre).exclude(id=grupo.id).exists():
            messages.error(request, f"Ya existe un grupo llamado «{nuevo_nombre}».")
        else:
            grupo.name = nuevo_nombre
            grupo.save()
            messages.success(request, "Grupo actualizado.")
            return redirect('grupos')
        return redirect('editar_grupo', id_grupo=grupo.id)

    return render(request, 'editar_grupo.html', {
        'grupo': grupo,
        'miembros': dar_miembros(grupo),
        'no_miembros': dar_no_miembros(grupo),
    })


@user_passes_test(es_admin)
@require_POST
def agregar_usuario_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)
    id_user = request.POST.get('id_user')
    if id_user:
        user = get_object_or_404(User, id=id_user)
        grupo.user_set.add(user)
        messages.success(request, f"{user.get_full_name() or user.username} se agregó al grupo.")
    return redirect('editar_grupo', id_grupo=grupo.id)


@user_passes_test(es_admin)
@require_POST
def eliminar_usuario_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)
    id_user = request.POST.get('id_user')
    if id_user:
        user = get_object_or_404(User, id=id_user)
        grupo.user_set.remove(user)
        messages.success(request, f"{user.get_full_name() or user.username} se quitó del grupo.")
    return redirect('editar_grupo', id_grupo=grupo.id)



