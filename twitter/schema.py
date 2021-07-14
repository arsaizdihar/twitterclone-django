import graphene
from graphene_django import DjangoListField
from graphql_auth import mutations
from users.schema import UserQuery, UserMutation, MeQuery, FollowQuery
from users.models import User
from tweet.schema import TweetQuery, TweetMutation


class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    update_account = mutations.UpdateAccount.Field()
    token_auth = mutations.ObtainJSONWebToken.Field()
    refresh_token = mutations.RefreshToken.Field()


class Query(UserQuery, MeQuery, TweetQuery, FollowQuery, graphene.ObjectType):
    pass


class Mutation(AuthMutation, TweetMutation, UserMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
