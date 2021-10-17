import graphene
from graphene_django import DjangoListField
from graphql_auth import mutations
from tweet.schema import TweetMutation, TweetQuery
from users.models import User
from users.schema import AcceptFollow, FollowQuery, MeQuery, UserMutation, UserQuery


class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    update_account = mutations.UpdateAccount.Field()
    token_auth = mutations.ObtainJSONWebToken.Field()
    refresh_token = mutations.RefreshToken.Field()


class Query(UserQuery, MeQuery, TweetQuery, FollowQuery, graphene.ObjectType):
    pass


class Mutation(
    AuthMutation, TweetMutation, UserMutation, AcceptFollow, graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
