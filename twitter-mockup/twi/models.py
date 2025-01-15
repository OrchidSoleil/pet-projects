from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Post(models.Model):
    text = models.TextField(blank=False, max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True)
    upvotes = models.IntegerField(blank=True, default=0)

    def serialize(self):
        return {
            "text": self.text,
            "author": self.author,
            "date_posted": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "upvotes": self.upvotes
        }


# https://stackoverflow.com/questions/58794639/how-to-make-follower-following-system-with-django-model
class Followers(models.Model):
    user = models.ForeignKey(User, related_name="following", on_delete=models.CASCADE)
    following_user = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)

    class Meta():
        unique_together = ('user', 'following_user')


class Like(models.Model):
    user = models.ForeignKey(User, related_name="user_likes", on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="post_likes", on_delete=models.CASCADE)

    class Meta():
        unique_together = ('user', 'post')
