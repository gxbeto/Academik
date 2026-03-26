from django.urls import path

from .views import (
    CrudEntidadDeleteView,
    CrudEntidadFormView,
    CrudEntidadImportView,
    CrudEntidadListView,
    InicioView,
)

urlpatterns = [
    path("", InicioView.as_view(), name="inicio"),
    path("crud/<slug:entity_key>/", CrudEntidadListView.as_view(), name="crud-entidad"),
    path(
        "crud/<slug:entity_key>/nuevo/",
        CrudEntidadFormView.as_view(),
        name="crud-entidad-nuevo",
    ),
    path(
        "crud/<slug:entity_key>/importar/",
        CrudEntidadImportView.as_view(),
        name="crud-entidad-importar",
    ),
    path(
        "crud/<slug:entity_key>/<int:pk>/editar/",
        CrudEntidadFormView.as_view(),
        name="crud-entidad-editar",
    ),
    path(
        "crud/<slug:entity_key>/<int:pk>/eliminar/",
        CrudEntidadDeleteView.as_view(),
        name="crud-entidad-eliminar",
    ),
]
