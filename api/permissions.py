from rest_framework import permissions


class IsInspectorOrDeveloper(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['inspector', 'developer']

    def has_object_permission(self, request, view, obj):
        return request.user.role in ['inspector', 'developer']