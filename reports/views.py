# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.response import Response
from braces.views import LoginRequiredMixin
from core.models import Course, CourseStudent, Class
from django.core.exceptions import ObjectDoesNotExist
from reports.serializer import UserCourseStatsSerializer, CourseStats, LessonUserStats


class UserCourseStats(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    model = CourseStudent
    serializer_class = UserCourseStatsSerializer
    filter_fields = ('course',)

    def get_queryset(self):
        queryset = super(UserCourseStats, self).get_queryset()
        user = self.request.user
        course_id = self.request.QUERY_PARAMS.get('course')
        role = None
        try:
            role = self.request.user.teaching_courses.get(course__id=course_id).role
        except ObjectDoesNotExist:
            pass

        classes_id = self.request.QUERY_PARAMS.getlist('classes')
        # class passed as get paremeter
        classes = Class.objects.filter(course=course_id)
        if classes_id:
            classes = classes.filter(id__in=classes_id)
            queryset = queryset.filter(user__classes__in=classes)
        if (role and role == 'coordinator') or self.request.user.is_staff or self.request.user.is_superuser:
            return queryset
        else:
            # if user is not coordinator or admin, only show his classes
            classes = classes.filter(assistant=user)
            return queryset.filter(user__classes__in=classes)


class UserCourseLessonsStats(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    model = CourseStudent
    serializer_class = LessonUserStats
    filter_fields = ('course', 'user',)
    lookup_field = 'course'


class CourseStatsByLessonViewSet(LoginRequiredMixin, viewsets.ReadOnlyModelViewSet):
    model = Course
    serializer_class = CourseStats

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()

        course_id = self.kwargs.get('pk')
        role = None
        try:
            role = self.request.user.teaching_courses.get(course__id=course_id).role
        except ObjectDoesNotExist:
            pass

        classes_id = self.request.QUERY_PARAMS.getlist('classes')
        # class passed as get paremeter
        classes = Class.objects.filter(course=course_id)
        if classes_id:
            classes = classes.filter(id__in=classes_id)
        # if user is not coordinator or admin, only show his classes
        if not (role and (role == 'coordinator') and self.request.user.is_staff and self.request.user.is_superuser):
            classes = classes.filter(assistant=self.request.user)

        self.object.classes = classes
        serializer = self.get_serializer(self.object)
        return Response(serializer.data)
