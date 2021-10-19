from django.db import models
from django.utils.translation import ugettext_lazy as _
from users.models import User


def get_image_directory(instance, filename: str):
    return f"tweet/{instance.user.id}/{filename}"


class Tweet(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tweets",
        related_query_name="tweets",
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    text = models.TextField(verbose_name=_("Tweet text"))
    comment_to = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="comments",
        related_query_name="comments",
        blank=True,
        null=True,
    )
    image = models.ImageField(upload_to=get_image_directory, null=True, blank=True)
    likes = models.ManyToManyField(
        User, related_name="likes", related_query_name="likes", blank=True
    )
    retweets = models.ManyToManyField(
        User, related_name="retweets", related_query_name="retweets", blank=True
    )

    def have_access(self, user: User):
        return not self.user.private or self.user == user or (user.is_authenticated and self.user.followers.filter(id=user.id).exists())

    class Meta:
        verbose_name = "Tweet"
        verbose_name_plural = "Tweets"
        ordering = ["-created_at"]
