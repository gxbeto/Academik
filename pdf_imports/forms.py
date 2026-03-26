from django import forms


class PdfImportForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo PDF",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".pdf,application/pdf",
                "class": (
                    "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm "
                    "text-slate-900 outline-none transition focus:border-rio focus:ring-0"
                ),
                "title": "Selecciona el archivo PDF que contiene la informacion a importar.",
            }
        ),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if not archivo.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Selecciona un archivo con extension .pdf.")
        return archivo
