from django.contrib import admin

from .models import Script, ScriptGroup, ScriptParameter, DjanguiJob, AddScript, ScriptParameterGroup



# class DjanguiAdmin(admin.AdminSite):
#     index_template = 'djangui_admin/index.html'
#
#     def get_urls(self):
#         urls = super(DjanguiAdmin, self).get_urls()
#         my_urls = [
#             url(r'^add-scripts/$', self.admin_view(self.add_scripts), name='add_scripts'),
#         ]
#         return my_urls + urls
#
#     def add_scripts(self, request):
#         # ...
#         context = dict(
#            # Include common variables for rendering the admin template.
#            self.each_context(request),
#            # Anything else you want in the context...
#             form=AddScriptForm,
#         )
#         return TemplateResponse(request, "djangui_admin/add_scripts.html", context)

# djangui_admin = DjanguiAdmin()
djangui_admin = admin.AdminSite()

class AddScriptsAdmin(admin.ModelAdmin):
    pass

djangui_admin.register(DjanguiJob, admin.ModelAdmin)
djangui_admin.register(Script, admin.ModelAdmin)
djangui_admin.register(ScriptParameter, admin.ModelAdmin)
djangui_admin.register(ScriptGroup, admin.ModelAdmin)
djangui_admin.register(AddScript, AddScriptsAdmin)
djangui_admin.register(ScriptParameterGroup, AddScriptsAdmin)