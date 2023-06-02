from __future__ import absolute_import
import os

from django.contrib.admin import ModelAdmin, site, TabularInline

from .models import (
    Script,
    ScriptVersion,
    ScriptGroup,
    ScriptParameter,
    ScriptParameterGroup,
    ScriptParser,
    UserFile,
    WooeyJob,
    WooeyWidget,
)


class JobAdmin(ModelAdmin):
    list_display = ("user", "job_name", "script_version", "status", "created_date")


class ScriptVersionInline(TabularInline):
    model = ScriptVersion
    extra = 1
    readonly_fields = ("created_date", "created_by", "modified_date", "modified_by")


class ScriptAdmin(ModelAdmin):
    list_display = ("script_name", "script_group", "is_active")
    inlines = [ScriptVersionInline]

    class Media:
        js = (os.path.join("wooey", "js", "admin", "script.js"),)


class ParameterAdmin(ModelAdmin):
    list_display = ("script_versions", "parameter_group", "short_param")

    def script_versions(self, obj):
        return ", ".join(
            [
                "{}: {}".format(
                    script_version.script.script_name, script_version.script_iteration
                )
                for script_version in obj.script_version.all()
            ]
        )


class GroupAdmin(ModelAdmin):
    list_display = ("group_name", "is_active")


class ParameterGroupAdmin(ModelAdmin):
    list_display = ("script_versions", "group_name")

    def script_versions(self, obj):
        return ", ".join(
            [
                "{}: {}".format(
                    script_version.script.script_name, script_version.script_iteration
                )
                for script_version in obj.script_version.all()
            ]
        )


class ScriptParserAdmin(ModelAdmin):
    list_display = ("script_versions", "subparser_command")

    def subparser_command(self, obj):
        return obj.name or "Main Entrypoint"

    subparser_command.short_description = "Subparser Command"
    subparser_command.admin_order_field = "name"

    def script_versions(self, obj):
        return ", ".join(
            [
                "{}: {}".format(
                    script_version.script.script_name, script_version.script_iteration
                )
                for script_version in obj.script_version.all()
            ]
        )


class ScriptVersionAdmin(ModelAdmin):
    list_display = (
        "script",
        "script_version",
        "script_iteration",
        "default_version",
        "created_by",
        "modified_by",
    )
    readonly_fields = ("created_date", "created_by", "modified_date", "modified_by")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super(ScriptVersionAdmin, self).save_model(request, obj, form, change)


class FileAdmin(ModelAdmin):
    pass


site.register(WooeyWidget)
site.register(WooeyJob, JobAdmin)
site.register(UserFile, FileAdmin)
site.register(Script, ScriptAdmin)
site.register(ScriptParameter, ParameterAdmin)
site.register(ScriptGroup, GroupAdmin)
site.register(ScriptParameterGroup, ParameterGroupAdmin)
site.register(ScriptParser, ScriptParserAdmin)
site.register(ScriptVersion, ScriptVersionAdmin)
