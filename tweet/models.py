from django.db import models
from users.models import User
from django.utils.translation import ugettext_lazy as _


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
    likes = models.ManyToManyField(
        User,
        related_name="likes",
        related_query_name="likes",
    )
    retweets = models.ManyToManyField(
        User, related_name="retweets", related_query_name="retweets"
    )

    class Meta:
        verbose_name = "Tweet"
        verbose_name_plural = "Tweets"
        ordering = ["-created_at"]
