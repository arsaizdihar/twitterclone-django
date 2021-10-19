import graphene
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import get_object_or_404
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphene_file_upload.scalars import Upload
from users.models import User
from users.schema import UserWithFollowNode

from .models import Tweet


class TweetNode(DjangoObjectType):
    class Meta:
        model = Tweet
        fields = "__all__"
        filter_fields = ("text", "user", "comment_to")
        interfaces = (graphene.relay.Node,)

    pk = graphene.Int()
    likes_count = graphene.Int()
    retweet_count = graphene.Int()
    comments_count = graphene.Int()
    user = graphene.Field(UserWithFollowNode)
    is_liked = graphene.Boolean()
    likes = DjangoFilterConnectionField(UserWithFollowNode)
    text = graphene.String()

    def resolve_pk(self, info):
        return self.pk

    def resolve_likes_count(self, info):
        return self.likes.count()

    def resolve_retweet_count(self, info):
        return self.retweets.count()

    def resolve_comments_count(self, info):
        return Tweet.objects.filter(comment_to__id=self.pk).count()

    def resolve_user(self, info):
        return self.user

    def resolve_likes(self, info):
        return self.likes

    def resolve_is_liked(self, info):
        return (
            info.context.user.is_authenticated
            and Tweet.objects.filter(id=self.pk)
            .filter(likes__id=info.context.user.id)
            .first()
            != None
        )

    def resolve_text(self, info):
        return self.text if self.have_access(info.context.user) else ""

    def resolve_image(self, info):
        if self.image and self.have_access(info.context.user):
            return f"{info.context.scheme}://{info.context.get_host()}{settings.MEDIA_URL}{self.image}"


class TweetQuery(graphene.ObjectType):
    tweets = DjangoFilterConnectionField(TweetNode, username=graphene.String(), exclude_comment=graphene.Boolean())
    tweet = graphene.Field(TweetNode, id=graphene.Int(required=True))

    def resolve_tweet(self, info, id=None):
        return get_object_or_404(Tweet, id=id)

    def resolve_tweets(
        self,
        info,
        first=None,
        after=None,
        comment_to=None,
        user=None,
        username=None,
        exclude_comment=None
    ):
        if exclude_comment:
            queryset = Tweet.objects.filter(comment_to=None)
        else:
            queryset = Tweet.objects
        if username is not None:
            requested_user = User.objects.filter(username=username).first()
            if not requested_user:
                return queryset.none()
            if requested_user.private and requested_user.id != info.context.user.id:
                if (
                    not info.context.user.is_authenticated
                    or not requested_user.followers.filter(
                        id=info.context.user.id
                    ).exists()
                ):
                    return queryset.none()
            return queryset.filter(user__username=username).all()
        if not info.context.user.is_authenticated:
            return queryset.none()

        if comment_to:
            if queryset.filter(id=comment_to).exists():
                return queryset.filter(comment_to__id=comment_to).all()
            else:
                return queryset.none()

        result = queryset.filter(
            user__in=info.context.user.following.all()
        ) | queryset.filter(user=info.context.user)
        return result.all()


class PostTweet(graphene.Mutation):
    tweet = graphene.Field(TweetNode)
    success = graphene.Boolean()

    class Arguments:
        comment_to = graphene.Int()
        text = graphene.String(required=True)
        file = Upload(required=False)

    @staticmethod
    def mutate(root, info, text, file: InMemoryUploadedFile = None, comment_to=None):
        if not info.context.user.is_authenticated:
            return None
        tweet_to_comment = Tweet.objects.filter(id=comment_to).first()
        new_tweet = Tweet(text=text, user=info.context.user, image=file, comment_to=tweet_to_comment)
        new_tweet.full_clean()
        new_tweet.save()
        return PostTweet(tweet=new_tweet, success=True)


class LikeMutation(graphene.Mutation):
    success = graphene.Boolean()
    is_liked = graphene.Boolean()

    class Arguments:
        tweet_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, tweet_id):
        if not info.context.user.is_authenticated:
            return None
        tweet_query = Tweet.objects.filter(id=tweet_id)
        if not tweet_query.first():
            return None
        liked = tweet_query.filter(likes__id=info.context.user.id).first()
        tweet = tweet_query.first()
        if liked:
            tweet.likes.remove(info.context.user)
        else:
            tweet.likes.add(info.context.user)
        return LikeMutation(success=True, is_liked=not liked)


class RetweetMutation(graphene.Mutation):
    success = graphene.Boolean()
    is_retweeted = graphene.Boolean()

    class Arguments:
        tweet_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, tweet_id):
        if not info.context.user.is_authenticated:
            return None
        tweet_query = Tweet.objects.filter(id=tweet_id)
        if not tweet_query.first():
            return None
        retweeted = tweet_query.filter(retweets__id=info.context.user.id).first()
        tweet = tweet_query.first()
        if retweeted:
            tweet.retweets.remove(info.context.user)
        else:
            tweet.retweets.add(info.context.user)
        return RetweetMutation(success=True, is_retweeted=not retweeted)


class TweetMutation(graphene.ObjectType):
    post_tweet = PostTweet.Field()
    like_tweet = LikeMutation.Field()
    retweet = RetweetMutation.Field()
