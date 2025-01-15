from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import F
import json

from .models import User, Post, Followers, Like
from django.forms import ModelForm


def index(request):
    new_post_form = NewPostForm()
    edit_post_form = EditPostForm()
    # authenticate list of user likes for unlogged users
    user_likes_list = []
    try:
        posts = Post.objects.all().order_by("-date_posted")
        if request.user.is_authenticated:
            # get a queryset for likes and make a list of it
            user_likes_object = Like.objects.filter(user=request.user)
            user_likes_list = like_list(user_likes_object)
    except Post.DoesNotExist:
        posts = {}
    # divide queryset into pages
    page_obj = pagination(request, posts)
    return render(request, "twi/index.html", {'form': new_post_form, 'edit_post_form': edit_post_form, 'page_obj': page_obj, 'likes': user_likes_list})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "twi/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "twi/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "twi/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "twi/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "twi/register.html")


class NewPostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text']
        labels = {
            "text": ""
        }


@login_required
def create_post(request):
    if request.method == "POST":
        form = NewPostForm(request.POST)
        if form.is_valid:
            post_instance = form.save(commit=False)
            post_instance.author = request.user
            post_instance.save()
            return redirect('index')
        else:
            # if form is invalid return the contents
            return render(request, "twi/index.html", {"form": form})
    form = NewPostForm(request.POST)
    return redirect('index')


class EditPostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text']
        labels = {'text': ""}


@login_required
def edit_post(request, post_id):
    current_user = request.user
    try:
        post_to_edit = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return render(request, 'twi/profile.html', {"message": "Post non-existent."})
    if post_to_edit.author != current_user:
        return JsonResponse({"message": "You can't edit other user's posts!", "new_text": post_to_edit.text})

    if request.method == "PUT":
        # using json, get edited text and send it to form for validation
        data = json.loads(request.body)
        form = EditPostForm(data)
        new_text = data['text']

        if form.is_valid:
            if data.get("text") is not None and len(new_text) > 0:
                post_to_edit.text = new_text
                post_to_edit.save()
                return JsonResponse({"message": "Successfully edited!", "new_text": new_text}, status=200)
            # don't let users leave the comment blank
            else:
                return JsonResponse({"message": "Can't be blank!", "new_text": post_to_edit.text})
    return render(request, 'twi/profile.html', {"message": "Unacceptable input."})


def like_unlike(request, post_id):
    current_user = request.user
    try:
        post_to_like = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return render(request, 'twi/profile.html', {"message": "Post non-existent."})

    if request.method == "PUT":
        # get json data from fetch request
        if not current_user.is_authenticated:
            return JsonResponse({"like": "<img src='/static/twi/unliked.png'>", "color": "grey", "amount": post_to_like.upvotes, "message": 'Log in to like.'}, status=200)
        data = json.loads(request.body)
        if data.get('like') is not None:
            if not Like.objects.filter(user=current_user, post=post_to_like).exists():
                Like.objects.create(user=current_user, post=post_to_like)
                Post.objects.filter(pk=post_to_like.id).update(upvotes=F('upvotes') + 1)
                post_to_like.refresh_from_db(fields=['upvotes'])
                like_amount = post_to_like.upvotes
                return JsonResponse({"like": "<img src='/static/twi/liked.png'>", "color": "pink", "amount": like_amount}, status=200)
            else:
                like_instance = Like.objects.filter(user=current_user, post=post_to_like)
                like_instance.delete()
                Post.objects.filter(pk=post_to_like.id).update(upvotes=F('upvotes') - 1)
                post_to_like.refresh_from_db(fields=['upvotes'])
                like_amount = post_to_like.upvotes
                return JsonResponse({"like": "<img src='/static/twi/unliked.png'>", "color": "grey", "amount": like_amount}, status=200)
    return JsonResponse({"like": "Like", "color": "grey"}, status=200)


def profile_page(request, username):
    # user = get_object_or_404(User, pk=user_id)
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return render(request, 'twi/profile.html', {"message": "Such user doesn't exist"})
    # get user followers and the ones user followed number
    all_following = user.following.all().count()
    all_followers = user.followers.all().count()
    # initialize list of followers
    followers = []
    if request.user.is_authenticated:
        followers = user.followers.filter(user=request.user)
    # check if user is a follower and change the name of a button
    is_follower = 'Follow'
    if len(followers) > 0:
        is_follower = 'Unfollow'
    posts = Post.objects.filter(author=user).order_by("-date_posted")
    # get likes list
    user_likes_list = []
    if request.user.is_authenticated:
        # get a queryset for likes and make a list of it
        user_likes_object = Like.objects.filter(user=request.user)
        user_likes_list = like_list(user_likes_object)
    # divide posts into pages
    page_obj = pagination(request, posts)
    # add edit form to edit posts
    edit_post_form = EditPostForm()
    return render(request, "twi/profile.html", {"profile_user": user, "is_follower": is_follower,
                                                "followers": all_followers, "number_of_following": all_following,
                                                "page_obj": page_obj, "likes": user_likes_list,
                                                'edit_post_form': edit_post_form})


def follow_user(request, user_id):
    try:
        follow_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"following": "Follow"}, status=201)
    # new_follower = Users.get_object_or_404(pk=user_id)
    if request.method == "PUT":
        if not Followers.objects.filter(user=request.user, following_user=follow_user).exists():
            Followers.objects.create(user=request.user, following_user=follow_user)
            return JsonResponse({"following": "Unfollow"}, status=200)
        else:
            follower = Followers.objects.filter(user=request.user, following_user=follow_user)
            follower.delete()
            return JsonResponse({"following": "Follow"}, status=200)
    return redirect('profile_page', user_id)


@login_required
def following(request):
    user = User.objects.get(username=request.user.username)
    # with list comprehension get users from the Followers object
    following_users = [f.following_user for f in user.following.all()]
    posts = Post.objects.filter(author__in=following_users).order_by("-date_posted")
    page_obj = pagination(request, posts)
    if request.user.is_authenticated:
        # get a queryset for likes and make a list of it
        user_likes_object = Like.objects.filter(user=request.user)
        user_likes_list = like_list(user_likes_object) if user_likes_object else []
    return render(request, "twi/posts.html", {"page_obj": page_obj, "likes": user_likes_list})


# utility functions
def like_list(queryset):
    # make a list of liked posts ids
    user_likes_list = [like.post.id for like in queryset]
    return user_likes_list


# https://docs.djangoproject.com/en/4.0/topics/pagination/
def pagination(request, queryset):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    if page_number is None:
        page_number = '1'
    page_obj = paginator.get_page(page_number)
    return page_obj
