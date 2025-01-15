
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create-post", views.create_post, name="create_post"),
    path("follow/<int:user_id>", views.follow_user, name="follow_user"),
    path("user-profile/<str:username>", views.profile_page, name="profile_page"),
    path("following", views.following, name="following"),
    path("edit-post/<int:post_id>", views.edit_post, name="edit_post"),
    path("like-unlike/<int:post_id>", views.like_unlike, name="like_unlike"),
]
