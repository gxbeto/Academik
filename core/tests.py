from datetime import date
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from academics.models import Alumno, AlumnoCurso, Curso, ProfesorCurso
from accounts.models import Profesor, Rol, Usuario
from pdf_imports.models import ImportacionPDF

from core.runtime_config import (
    build_local_dev_csrf_trusted_origins,
    expand_local_dev_hosts,
)


class RuntimeConfigTests(SimpleTestCase):
    @patch(
        "core.runtime_config._discover_local_host_candidates",
        return_value=["localhost", "192.168.0.11", "academik.local"],
    )
    def test_expand_local_dev_hosts_adds_detected_hosts_in_debug(self, mocked_discovery):
        hosts = expand_local_dev_hosts(["127.0.0.1", "localhost"], debug=True)

        self.assertEqual(
            hosts,
            ["127.0.0.1", "localhost", "192.168.0.11", "academik.local"],
        )
        mocked_discovery.assert_called_once()

    def test_expand_local_dev_hosts_keeps_input_outside_debug(self):
        hosts = expand_local_dev_hosts(["127.0.0.1", "localhost"], debug=False)

        self.assertEqual(hosts, ["127.0.0.1", "localhost"])

    def test_build_local_dev_csrf_trusted_origins_adds_schemes_and_dev_port(self):
        origins = build_local_dev_csrf_trusted_origins(
            ["http://192.168.0.11:8000"],
            allowed_hosts=["127.0.0.1", "192.168.0.11", "academik.local"],
            debug=True,
        )

        self.assertEqual(
            origins,
            [
                "http://192.168.0.11:8000",
                "http://127.0.0.1",
                "http://127.0.0.1:8000",
                "https://127.0.0.1",
                "https://127.0.0.1:8000",
                "http://192.168.0.11",
                "https://192.168.0.11",
                "https://192.168.0.11:8000",
                "http://academik.local",
                "http://academik.local:8000",
                "https://academik.local",
                "https://academik.local:8000",
            ],
        )


class CrudWorkflowTests(TestCase):
    def setUp(self):
        self.rol, _ = Rol.objects.get_or_create(
            nombre=Rol.Nombres.ADMINISTRADOR,
            defaults={"descripcion": "Acceso completo"},
        )
        self.profesor_rol, _ = Rol.objects.get_or_create(
            nombre=Rol.Nombres.PROFESOR,
            defaults={"descripcion": "Acceso docente"},
        )
        self.usuario = Usuario.objects.create_user(
            username="gestor",
            password="admin12345",
            rol=self.rol,
            activo=True,
        )
        self.profesor_usuario = Usuario.objects.create_user(
            username="docente",
            password="admin12345",
            rol=self.profesor_rol,
            activo=True,
        )
        self.profesor = Profesor.objects.create(
            usuario=self.profesor_usuario,
            cedula="1234567",
            nombres="Juan",
            apellidos="Perez",
            activo=True,
        )
        self.otro_profesor_usuario = Usuario.objects.create_user(
            username="docente2",
            password="admin12345",
            rol=self.profesor_rol,
            activo=True,
        )
        self.otro_profesor = Profesor.objects.create(
            usuario=self.otro_profesor_usuario,
            cedula="7654321",
            nombres="Laura",
            apellidos="Fernandez",
            activo=True,
        )
        self.curso_profesor = Curso.objects.create(
            codigo="CUR-001",
            nombre="Primer Curso",
            seccion="A",
            turno="Manana",
            periodo_lectivo="2026",
            activo=True,
        )
        self.otro_curso = Curso.objects.create(
            codigo="CUR-002",
            nombre="Segundo Curso",
            seccion="B",
            turno="Tarde",
            periodo_lectivo="2026",
            activo=True,
        )
        self.asignacion_visible = ProfesorCurso.objects.create(
            profesor=self.profesor,
            curso=self.curso_profesor,
            titular=True,
            activo=True,
            fecha_desde=date(2026, 3, 1),
        )
        self.asignacion_oculta = ProfesorCurso.objects.create(
            profesor=self.otro_profesor,
            curso=self.otro_curso,
            titular=False,
            activo=True,
            fecha_desde=date(2026, 3, 5),
        )
        self.alumno_visible = Alumno.objects.create(
            documento="100",
            nombres="Ana",
            apellidos="Lopez",
            activo=True,
        )
        self.alumno_oculto = Alumno.objects.create(
            documento="200",
            nombres="Bruno",
            apellidos="Gomez",
            activo=True,
        )
        AlumnoCurso.objects.create(
            alumno=self.alumno_visible,
            curso=self.curso_profesor,
            fecha_ingreso=date(2026, 3, 1),
            estado=AlumnoCurso.Estados.ACTIVO,
        )
        AlumnoCurso.objects.create(
            alumno=self.alumno_oculto,
            curso=self.otro_curso,
            fecha_ingreso=date(2026, 3, 1),
            estado=AlumnoCurso.Estados.ACTIVO,
        )
        self.client.force_login(self.usuario)

    def test_list_page_shows_create_button_and_rows(self):
        response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo registro")
        self.assertNotContains(response, "Importar PDF")
        self.assertContains(response, "Registros cargados")
        self.assertNotContains(response, "Completa los datos")
        self.assertContains(response, "Eliminar")

    def test_role_can_be_created_from_form_page(self):
        response = self.client.post(
            reverse("crud-entidad-nuevo", kwargs={"entity_key": "roles"}),
            {
                "nombre": "COORDINADOR",
                "descripcion": "Coordina cursos y profesores",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("crud-entidad", kwargs={"entity_key": "roles"}))
        self.assertTrue(Rol.objects.filter(nombre="COORDINADOR").exists())

    def test_role_can_be_updated_from_edit_page(self):
        role = Rol.objects.create(
            nombre="SECRETARIA",
            descripcion="Gestiona recepcion",
            activo=True,
        )
        response = self.client.post(
            reverse("crud-entidad-editar", kwargs={"entity_key": "roles", "pk": role.pk}),
            {
                "nombre": "SECRETARIA GENERAL",
                "descripcion": "Gestiona recepcion y documentos",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("crud-entidad", kwargs={"entity_key": "roles"}))
        role.refresh_from_db()
        self.assertEqual(role.nombre, "SECRETARIA GENERAL")

    def test_role_can_be_deleted_from_list(self):
        role = Rol.objects.create(
            nombre="TEMPORAL",
            descripcion="Se eliminara",
            activo=True,
        )
        response = self.client.post(
            reverse("crud-entidad-eliminar", kwargs={"entity_key": "roles", "pk": role.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Rol.objects.filter(pk=role.pk).exists())
        self.assertContains(response, "El registro fue eliminado correctamente.")

    def test_delete_shows_integrity_error_when_record_is_in_use(self):
        response = self.client.post(
            reverse("crud-entidad-eliminar", kwargs={"entity_key": "roles", "pk": self.rol.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Rol.objects.filter(pk=self.rol.pk).exists())
        self.assertContains(
            response,
            "No se puede eliminar este registro porque esta siendo usado en otros datos relacionados.",
        )

    def test_list_page_hides_old_technical_copy(self):
        response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tabla fisica")
        self.assertNotContains(response, "Columnas visibles")
        self.assertNotContains(response, "Registros detectados")
        self.assertNotContains(response, "CRUD")
        self.assertContains(response, "Toca una fila para abrirla y actualizar sus datos.")

    def test_new_form_uses_tooltips_and_hides_help_block(self):
        response = self.client.get(reverse("crud-entidad-nuevo", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ayuda rapida")
        self.assertContains(response, "tooltip-badge")
        self.assertContains(response, 'class="crud-inline-field"', html=False)
        self.assertContains(response, 'class="crud-inline-field-label"', html=False)
        self.assertContains(response, 'class="crud-inline-field-control"', html=False)

    def test_boolean_fields_render_as_toggle_switches(self):
        response = self.client.get(reverse("crud-entidad-nuevo", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="crud-inline-field toggle-field"', html=False)
        self.assertContains(response, 'class="crud-inline-field-label"', html=False)
        self.assertContains(
            response,
            'class="crud-inline-field-control crud-inline-field-control-toggle"',
            html=False,
        )
        self.assertContains(response, 'class="toggle-switch-input"', html=False)
        self.assertContains(response, 'class="toggle-switch-track"', html=False)
        self.assertContains(response, 'role="switch"', html=False)

    def test_admin_only_sees_import_button_for_professors_and_students(self):
        profesores_response = self.client.get(
            reverse("crud-entidad", kwargs={"entity_key": "profesores"})
        )
        alumnos_response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "alumnos"}))
        roles_response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "roles"}))

        self.assertContains(profesores_response, "Importar PDF")
        self.assertContains(alumnos_response, "Importar PDF")
        self.assertNotContains(roles_response, "Importar PDF")

    def test_non_admin_cannot_open_import_screen(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(
            reverse("crud-entidad-importar", kwargs={"entity_key": "profesores"})
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_cannot_open_import_screen_for_non_importable_entity(self):
        response = self.client.get(
            reverse("crud-entidad-importar", kwargs={"entity_key": "roles"})
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_process_pdf_import_placeholder(self):
        response = self.client.post(
            reverse("crud-entidad-importar", kwargs={"entity_key": "profesores"}),
            {
                "action": "process",
                "archivo": SimpleUploadedFile(
                    "profesores.pdf",
                    b"%PDF-1.4 placeholder",
                    content_type="application/pdf",
                ),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El archivo fue procesado.")
        self.assertContains(response, "El importador PDF de profesores aun no fue implementado.")
        self.assertTrue(ImportacionPDF.objects.filter(tipo_importacion="profesores").exists())

    def test_admin_can_discard_processed_import(self):
        importacion = ImportacionPDF.objects.create(
            nombre_archivo="profesores.pdf",
            ruta_archivo="imports/profesores/profesores.pdf",
            tipo_importacion="profesores",
            estado=ImportacionPDF.Estados.PROCESADO,
            total_registros=1,
            total_ok=0,
            total_error=1,
            usuario=self.usuario,
        )

        response = self.client.post(
            reverse("crud-entidad-importar", kwargs={"entity_key": "profesores"}),
            {
                "action": "discard",
                "import_id": importacion.id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ImportacionPDF.objects.filter(pk=importacion.pk).exists())
        self.assertContains(response, "La importacion fue descartada.")

    def test_sidebar_uses_compact_navigation_layout(self):
        response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Academi-k")
        self.assertContains(response, "dynamic-island-compact")
        self.assertContains(response, "Usuario activo")
        self.assertContains(response, self.usuario.get_short_name())
        self.assertContains(response, "Roles")
        self.assertContains(response, "Salir")
        self.assertContains(response, 'aria-label="Abrir menu"', html=False)
        self.assertContains(response, 'aria-label="Cerrar menu"', html=False)
        self.assertContains(response, 'aria-label="Cerrar sesion"', html=False)
        self.assertContains(response, '@click="menuOpen = false"', html=False)
        self.assertNotContains(response, '<p class="menu-section-title">Principal</p>', html=True)
        self.assertNotContains(response, '<span class="sidebar-link-label">Inicio</span>', html=True)
        self.assertNotContains(response, "sidebar-link-copy")

    def test_professor_home_hides_restricted_sections(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/crud/roles/"')
        self.assertNotContains(response, 'href="/crud/usuarios/"')
        self.assertNotContains(response, 'href="/crud/profesores/"')
        self.assertNotContains(response, 'href="/crud/matriculas/"')
        self.assertNotContains(response, 'href="/crud/importaciones-pdf/"')
        self.assertNotContains(response, 'href="/crud/detalle-importacion/"')
        self.assertNotContains(response, 'href="/crud/auditoria/"')
        self.assertContains(response, 'href="/crud/alumnos/"')

    def test_professor_cannot_open_restricted_crud(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "roles"}))

        self.assertEqual(response.status_code, 404)

    def test_professor_only_sees_students_from_associated_courses(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(reverse("crud-entidad", kwargs={"entity_key": "alumnos"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lopez")
        self.assertNotContains(response, "Gomez")

    def test_professor_cannot_edit_student_outside_associated_courses(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(
            reverse(
                "crud-entidad-editar",
                kwargs={"entity_key": "alumnos", "pk": self.alumno_oculto.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_professor_cannot_create_restricted_entities(self):
        self.client.force_login(self.profesor_usuario)

        for entity_key in ("alumnos", "cursos", "asignaciones-profesor"):
            with self.subTest(entity_key=entity_key):
                list_response = self.client.get(
                    reverse("crud-entidad", kwargs={"entity_key": entity_key})
                )
                create_response = self.client.get(
                    reverse("crud-entidad-nuevo", kwargs={"entity_key": entity_key})
                )

                self.assertEqual(list_response.status_code, 200)
                self.assertNotContains(list_response, "Nuevo registro")
                self.assertEqual(create_response.status_code, 404)

    def test_professor_only_sees_own_assignments(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(
            reverse("crud-entidad", kwargs={"entity_key": "asignaciones-profesor"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.profesor))
        self.assertContains(response, str(self.curso_profesor))
        self.assertNotContains(response, str(self.otro_profesor))
        self.assertNotContains(response, str(self.otro_curso))

    def test_professor_cannot_edit_assignment_of_another_teacher(self):
        self.client.force_login(self.profesor_usuario)

        response = self.client.get(
            reverse(
                "crud-entidad-editar",
                kwargs={
                    "entity_key": "asignaciones-profesor",
                    "pk": self.asignacion_oculta.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 404)
