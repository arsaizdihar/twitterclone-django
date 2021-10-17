import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField
from graphql_auth.schema import UserNode
from graphql_jwt.shortcuts import create_refresh_token, get_token

from .models import User

# class UserType(DjangoObjectType):
#     class Meta:
#         model = User


class UserWithFollowNode(UserNode):
    class Meta:
        model = User
        filter_fields = {
            "email": [
                "exact",
            ],
            "username": ["exact", "icontains", "istartswith"],
            "is_active": ["exact"],
            "status__archived": ["exact"],
            "status__verified": ["exact"],
            "status__secondary_email": ["exact"],
            "following": ["exact"],
            "followers": ["exact"],
        }
        exclude = ("password", "is_superuser")
        interfaces = (graphene.relay.Node,)
        skip_registry = True

    followers_count = graphene.Int()
    following_count = graphene.Int()
    is_self = graphene.Boolean()
    is_followed = graphene.Boolean()
    is_following = graphene.Boolean()
    is_requested = graphene.Boolean()

    def resolve_followers_count(self, info):
        return self.followers.count()

    def resolve_following_count(self, info):
        return self.following.count()

    def resolve_is_self(self, info):
        if not info.context.user.is_authenticated:
            return False
        return self.pk == info.context.user.id

    def resolve_is_followed(self, info):
        if not info.context.user.is_authenticated:
            return False
        return (
            User.objects.filter(id=self.pk)
            .filter(followers__id=info.context.user.id)
            .first()
            is not None
        )

    def resolve_is_following(self, info):
        if not info.context.user.is_authenticated:
            return False
        return (
            User.objects.filter(id=self.pk)
            .filter(following__id=info.context.user.id)
            .first()
            is not None
        )

    def resolve_is_requested(self, info):
        if not info.context.user.is_authenticated:
            return False
        return (
            User.objects.filter(id=self.pk)
            .filter(follow_requests=info.context.user)
            .exists()
        )


class UserQuery(graphene.ObjectType):
    user = graphene.Field(UserWithFollowNode, username=graphene.String(required=True))
    users = DjangoFilterConnectionField(UserWithFollowNode)

    def resolve_user(self, info, username=None):
        return User.objects.filter(username=username).first()


class FollowQuery(graphene.ObjectType):
    followers = DjangoFilterConnectionField(
        UserWithFollowNode, uname=graphene.String(required=True)
    )
    following = DjangoFilterConnectionField(
        UserWithFollowNode, uname=graphene.String(required=True)
    )
    unfollowed = DjangoFilterConnectionField(UserWithFollowNode)

    def resolve_followers(self, info, uname):
        user = User.objects.filter(username=uname).first()
        if not user:
            raise Exception("User doesn't exists")
        return user.followers.all()

    def resolve_following(self, info, uname):
        user = User.objects.filter(username=uname).first()
        if not user:
            raise Exception("User doesn't exists")
        return user.following.all()

    def resolve_unfollowed(self, info):
        if not info.context.user.is_authenticated:
            return None
        return (
            User.objects.exclude(followers__id=info.context.user.id)
            .exclude(id=info.context.user.id)
            .exclude(private=True)
        )


class MeQuery(graphene.ObjectType):
    me = graphene.Field(UserWithFollowNode)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None


class FollowCount(graphene.ObjectType):
    followers_count = graphene.Int(user_id=graphene.String())
    following_count = graphene.Int(user_id=graphene.String())

    def resolve_followers_count(self, info, user_id):
        return User.objects.filter(id=user_id).first().followers.count()

    def resolve_following_count(self, info, user_id):
        return User.objects.filter(id=user_id).first().following.count()


class AcceptFollow(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        user_id = graphene.Int(required=True)

    @staticmethod
    def mutate(cls, info, user_id):
        if (
            not info.context.user.is_authenticated
            or int(user_id) == info.context.user.id
        ):
            return None
        user_query = User.objects.filter(id=user_id)
        user = user_query.first()
        if not user:
            return None
        is_follower = info.context.user.followers.filter(id=user_id).exists()
        is_requested = info.context.user.follow_requests.filter(id=user_id).exists()
        if is_requested:
            info.context.user.follow_requests.remove(user)
            if not is_follower:
                info.context.user.followers.add(user)
            return cls(success=True)
        else:
            return cls(success=is_follower)


class FollowUser(graphene.Mutation):
    success = graphene.Boolean()
    is_followed = graphene.Boolean()
    user = graphene.Field(UserWithFollowNode)
    is_requested = graphene.Boolean()

    class Arguments:
        user_id = graphene.Int(required=True)

    @staticmethod
    def mutate(cls, info, user_id):
        if (
            not info.context.user.is_authenticated
            or int(user_id) == info.context.user.id
        ):
            return None
        user_query = User.objects.filter(id=user_id)
        if not user_query.first():
            return None
        followed = user_query.filter(followers__id=info.context.user.id).exists()
        user: User = user_query.first()
        if followed:
            user.followers.remove(info.context.user)
        else:
            if user.private:
                requested = user_query.filter(follow_requests__id=info.context.user.id)
                if requested:
                    user.follow_requests.remove(info.context.user)
                else:
                    user.follow_requests.add(info.context.user)
                return FollowUser(
                    success=True,
                    is_followed=False,
                    user=user,
                    is_requested=not requested,
                )
            user.followers.add(info.context.user)
        return FollowUser(
            success=True, is_followed=not followed, user=user, is_requested=False
        )


class UserMutation(graphene.ObjectType):
    follow = FollowUser.Field()
    accept_follow = AcceptFollow.Field()


# class RegisterMutation(graphene.Mutation):
#     user = graphene.Field(UserType)
#     success = graphene.Boolean()
#     token = graphene.String()
#     refresh_token = graphene.String()

#     class Arguments:
#         email = graphene.String(required=True)
#         username = graphene.String(required=True)
#         displayName = graphene.String(required=True)
#         password1 = graphene.String(required=True)
#         password2 = graphene.String(required=True)

#     @staticmethod
#     def mutate(root, info, email, username, displayName, password1, password2):
#         if password1 != password2:
#             raise Exception({"password": ["Password doesn't match"]})
#         user = User.objects.filter(username=username.lower()).first()
#         if user:
#             raise Exception({"username": ["Username Already Exists!"]})
#         user = User.objects.filter(email=email).first()
#         if user:
#             raise Exception({"email": ["Email Already Exists!"]})
#         else:
#             user = User(
#                 username=username.lower(), email=email, display_name=displayName
#             )
#             user.set_password(password1)
#             user.clean_fields()
#             user.save()
#             token = get_token(user)
#             refresh_token = create_refresh_token(user)
#             return RegisterMutation(
#                 user=user,
#                 token=token,
#                 refresh_token=refresh_token,
#                 success=True,
#             )
