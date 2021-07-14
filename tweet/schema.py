import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField
from .models import Tweet
from users.schema import UserWithFollowNode


class TweetNode(DjangoObjectType):
    class Meta:
        model = Tweet
        fields = "__all__"
        filter_fields = "__all__"
        interfaces = (graphene.relay.Node,)

    pk = graphene.Int()
    likes_count = graphene.Int()
    retweet_count = graphene.Int()
    user = graphene.Field(UserWithFollowNode)
    is_liked = graphene.Boolean()
    likes = DjangoFilterConnectionField(UserWithFollowNode)

    def resolve_pk(self, info):
        return self.pk

    def resolve_likes_count(self, info):
        return self.likes.count()

    def resolve_retweet_count(self, info):
        return self.retweets.count()

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


class TweetQuery(graphene.ObjectType):
    tweets = DjangoFilterConnectionField(TweetNode, username=graphene.String())
    tweet = graphene.relay.Node.Field(TweetNode)

    def resolve_tweets(
        self,
        info,
        first=None,
        after=None,
        comment_to=None,
        user=None,
        username=None,
    ):
        print(username)
        if username is not None:
            return Tweet.objects.filter(user__username=username).all()
        if not info.context.user.is_authenticated:
            return None
        result = Tweet.objects.filter(
            user__in=info.context.user.following.all()
        ) | Tweet.objects.filter(user=info.context.user)
        return result.all()


class PostTweet(graphene.Mutation):
    tweet = graphene.Field(TweetNode)
    success = graphene.Boolean()

    class Arguments:
        text = graphene.String(required=True)

    @staticmethod
    def mutate(root, info, text):
        if not info.context.user.is_authenticated:
            return None
        new_tweet = Tweet(text=text, user=info.context.user)
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
