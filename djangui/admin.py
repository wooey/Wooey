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
# djangui_admin = admin.AdminSite()

class AddScriptsAdmin(admin.ModelAdmin):
    pass

admin.site.register(DjanguiJob, admin.ModelAdmin)
admin.site.register(Script, admin.ModelAdmin)
admin.site.register(ScriptParameter, admin.ModelAdmin)
admin.site.register(ScriptGroup, admin.ModelAdmin)
admin.site.register(AddScript, AddScriptsAdmin)
admin.site.register(ScriptParameterGroup, AddScriptsAdmin)