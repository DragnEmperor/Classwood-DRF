"""
View mixins for common patterns across the API.
"""

from rest_framework.exceptions import NotFound

from api.models import SchoolModel, SessionModel, StaffModel, StudentModel


class SchoolContextMixin:
    """
    Resolves the school and active session from the authenticated user.
    Injects them into the serializer context so serializers can use
    ``self.context['school']`` and ``self.context['session']``.
    """

    def get_school(self):
        user = self.request.user
        try:
            return SchoolModel.objects.get(user=user)
        except SchoolModel.DoesNotExist:
            pass
        try:
            return StaffModel.objects.get(user=user).school
        except StaffModel.DoesNotExist:
            pass
        try:
            return StudentModel.objects.get(user=user).school
        except StudentModel.DoesNotExist:
            raise NotFound("No school associated with this account.") from None

    def get_active_session(self, school):
        session_id = self.request.query_params.get("session") or self.request.data.get("session")
        if session_id:
            try:
                return SessionModel.objects.get(id=session_id, school=school)
            except SessionModel.DoesNotExist:
                raise NotFound("Session not found.") from None
        return SessionModel.objects.filter(school=school, is_active=True).order_by("-start_date").first()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            school = self.get_school()
            context["school"] = school
            context["session"] = self.get_active_session(school)
        return context
