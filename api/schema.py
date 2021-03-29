import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
import graphql_jwt
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
from graphql_jwt.decorators import login_required
from graphql_relay import from_global_id
from .models import Tag, Blog
import pytz
from django_filters import FilterSet, OrderingFilter


class BlogFilter(FilterSet):
    class Meta:
        model = Blog
        fields = {
        }
    order_by = OrderingFilter(
        fields=(
            'created_at',
        )
    )


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        filter_fields = {
            'username': ['exact', 'icontains'],
        }
        interfaces = (relay.Node,)


class TagNode(DjangoObjectType):
    class Meta:
        model = Tag
        filter_fields = {
            'name': ['icontains'],
        }
        interfaces = (relay.Node,)


class TokyoDateTime(graphene.types.Scalar):
    @staticmethod
    def serialize(obj):
        timezone = pytz.timezone('Asia/Tokyo')
        return obj.astimezone(tz=timezone).strftime("%Y-%m-%d %H:%M:%S")


class BlogNode(DjangoObjectType):
    class Meta:
        model = Blog
        filter_fields = {
            'user__username': ['icontains'],
        }
        interfaces = (relay.Node,)
    created_at = graphene.Field(TokyoDateTime)


class CreateUserMutation(relay.ClientIDMutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    user = graphene.Field(UserNode)

    def mutate_and_get_payload(root, info, **input):
        user = User(
            username=input.get('username'),
            email=input.get('email'),
        )
        user.set_password(input.get('password'))
        user.save()

        return CreateUserMutation(user=user)


class CreateTagMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)

    tag = graphene.Field(TagNode)

    @login_required
    def mutate_and_get_payload(root, info, **input):
        tag = Tag(
            user_id = info.context.user.id,
            name = input.get('name')
        )
        tag.save()

        return CreateTagMutation(tag=tag)


class DeleteTagMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    tag = graphene.Field(TagNode)

    @login_required
    def mutate_and_get_payload(root, info, **input):
        tag = Tag(
            id=from_global_id(input.get('id'))[1]
        )
        tag.delete()

        return DeleteTagMutation(tag=tag)


class CreateBlogMutation(relay.ClientIDMutation):
    class Input:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        tags = graphene.List(graphene.ID)

    blog = graphene.Field(BlogNode)

    @login_required
    def mutate_and_get_payload(root, info, **input):
        blog = Blog(
            user_id = info.context.user.id,
            title = input.get('title'),
            content = input.get('content'),
        )
        blog.save()
        blog_comp = Blog.objects.get(id=blog.id)
        if input.get('tags') is not None:
            tags_set = []
            for tag in input.get('tags'):
                tag_id = from_global_id(tag)[1]
                tags_object = Tag.objects.get(id=tag_id)
                tags_set.append(tags_object)
            blog_comp.tags.set(tags_set)
        
        return CreateBlogMutation(blog=blog_comp)


class UpdateBlogMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        tags = graphene.List(graphene.ID)
        title = graphene.String()
        content = graphene.String()

    blog = graphene.Field(BlogNode)

    @login_required
    def mutate_and_get_payload(root, info, **input):
        blog = Blog.objects.get(id=from_global_id(input.get('id'))[1])
        if input.get('title') is not None:
            blog.title = input.get('title')
        if input.get('content') is not None:
            blog.content = input.get('content')         
        if input.get('tags') is not None:
            tags_set = []
            for tag in input.get('tags'):
                tag_id = from_global_id(tag)[1]
                tags_object = Tag.objects.get(id=tag_id)
                tags_set.append(tags_object)
            blog.tags.set(tags_set)
        blog.save()

        return UpdateBlogMutation(blog=blog)


class DeleteBlogMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    blog = graphene.Field(BlogNode)

    @login_required
    def mutate_and_get_payload(root, info, **input):

        blog = Blog(
            id=from_global_id(input.get('id'))[1]
        )
        blog.delete()

        return DeleteBlogMutation(blog=blog)


class Mutation(graphene.AbstractType):
    create_user = CreateUserMutation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    create_tag = CreateTagMutation.Field()
    delete_tag = DeleteTagMutation.Field()
    create_blog = CreateBlogMutation.Field()
    update_blog = UpdateBlogMutation.Field()
    delete_blog = DeleteBlogMutation.Field()


class Query(graphene.ObjectType):
    login_user = graphene.Field(UserNode)
    tag = relay.Node.Field(TagNode)
    blog = relay.Node.Field(BlogNode)
    all_tags = DjangoFilterConnectionField(TagNode)
    all_blogs = DjangoFilterConnectionField(BlogNode, filterset_class=BlogFilter)

    @login_required
    def resolve_login_user(self, info, **kwargs):
        return User.objects.get(id=info.context.user.id)














