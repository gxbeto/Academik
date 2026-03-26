from django.db import models


class ModeloCreado(models.Model):
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ModeloTrazable(ModeloCreado):
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
