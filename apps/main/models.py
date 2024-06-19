import os

import auto_prefetch

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from auditlog.registry import auditlog
from model_utils.models import TimeStampedModel

from apps.main.consts import ContactStatus


class TermsAndConditions(models.Model):
    """
    Model for the Terms and Conditions
    """

    terms = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Terms And Conditions created at {self.created_at}"

    class Meta:
        verbose_name = "Terms and Conditions"
        verbose_name_plural = "Terms and Conditions"


class PrivacyPolicy(models.Model):
    """
    Model for the Privacy Policy
    """

    policy = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Privacy Policy created at {self.created_at}"


class Contact(models.Model):
    """
    Model representing a user's contact request.
    """

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    contact_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, default=ContactStatus.PENDING.value)
    resolved_date = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=50)
    admin_notes = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        """
        Return a string representation of the model.
        """
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ["-contact_date"]
        verbose_name = "Contact Request"
        verbose_name_plural = "Contact Requests"


class AuditLogConfig(models.Model):
    """
    Model to store the configurations for models to be tracked by django-auditlog.
    """

    model_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.model_name

    def register_model(self):
        """
        Register the model with django-auditlog.
        :return:
        """
        try:
            model = apps.get_model(self.model_name)
            auditlog.register(model)
        except LookupError:
            pass  # Model not found, handle appropriately

    def unregister_model(self):
        """
        Unregister the model with django-auditlog.
        :return:
        """
        try:
            model = apps.get_model(self.model_name)
            auditlog.unregister(model)
        except LookupError:
            pass  # Model not found, handle appropriately


class SocialMediaLink(models.Model):
    """
    Model to store social media links for the organization.
    """

    platform_name = models.CharField(max_length=100)
    profile_url = models.URLField()
    image = models.ImageField(upload_to="social_media_images/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform_name} link"


class FAQ(models.Model):
    """
    Model for the FAQ
    """

    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"


class Report(auto_prefetch.Model):
    """
    A flexible report model for reporting inappropriate content across various models.

    Attributes:
        content_type (ContentType): The type of object being reported.
        object_id (int): The primary key of the related object being reported.
        content_object (GenericForeignKey): The generic foreign key to the related object.
        reporter (ForeignKey): The user who created the report.
        reason (TextField): The reason for the report.
        created_at (DateTimeField): The datetime when the report was created.
    """

    content_type = auto_prefetch.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    reporter = auto_prefetch.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="reports"
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(auto_prefetch.Model):
    """
    Notification model to handle user notifications.

    Attributes:
        user (User): The user to whom the notification belongs.
        title (str): The title of the notification.
        message (str): The message content of the notification.
        link (str): The URL to which the notification redirects.
        is_read (bool): Flag to check if the notification has been read.
        created_at (DateTimeField): The time the notification was created.
        updated_at (DateTimeField): The time the notification was last updated.
    """

    user = auto_prefetch.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TYPES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("danger", "Danger"),
        ("success", "Success"),
    ]
    type = models.CharField(max_length=10, choices=TYPES, default="info")

    def get_absolute_url(self) -> str:
        """
        Get the URL that allows users to mark the notification as read
        and be redirected to the destination URL.

        The link is URL-encoded to safely include it as a URL parameter.

        :return: URL as a string
        """
        return reverse(
            "mark_as_read_and_redirect",
            kwargs={"notification_id": self.pk, "destination_url": self.link},
        )

    def mark_as_read(self) -> None:
        """
        Mark the notification as read.
        """
        self.is_read = True
        self.save()

    def __str__(self) -> str:
        return self.title


class MediaLibrary(TimeStampedModel, models.Model):
    """
    MediaLibrary model to store images associated with any other model.

    Attributes:
        file (ImageField): The image file to be stored.
        content_type (ForeignKey): Reference to the ContentType of the related model.
        object_id (PositiveIntegerField): ID of the related model instance.
        content_object (GenericForeignKey): Generic relation to the related model.
    """

    file = models.ImageField(upload_to="media_library/")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self) -> str:
        """
        Returns the base name of the file.
        """
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = "Media Library"
        verbose_name_plural = "Media Libraries"


class Comment(TimeStampedModel, auto_prefetch.Model):
    """
    Represents a comment in the system.
    """

    content = models.CharField(max_length=1000, default="", verbose_name="Content")
    user = auto_prefetch.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="User",
    )

    content_type = auto_prefetch.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"Comment {self.id} by {self.user.username}"

    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created"]
