from django.urls import path
from .views import HomePage, VotePostView, PostDetailView, MyPostsView

urlpatterns = [
    path("", HomePage.as_view(), name="homepage"),
    path('votes/posts/<int:post_id>', VotePostView.as_view(), name='vote_post'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('myposts/', MyPostsView.as_view(), name='myposts'),
]