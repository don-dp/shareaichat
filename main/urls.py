from django.urls import path
from .views import HomePage, VotePostView, PostDetailView, MyPostsView, VoteCommentView, MyCommentsView, AddCommentView, ReplyCommentView, EditCommentView, CreatePostView

urlpatterns = [
    path("", HomePage.as_view(), name="homepage"),
    path('votes/posts/<int:post_id>', VotePostView.as_view(), name='vote_post'),
    path('votes/comments/<int:comment_id>', VoteCommentView.as_view(), name='vote_comment'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('myposts/', MyPostsView.as_view(), name='myposts'),
    path('mycomments/', MyCommentsView.as_view(), name='mycomments'),
    path('comments/add/<int:post_id>', AddCommentView.as_view(), name='add_comment'),
    path('comments/reply/<int:comment_id>', ReplyCommentView.as_view(), name='reply_comment'),
    path('comments/edit/<int:comment_id>', EditCommentView.as_view(), name='edit_comment'),
    path('createpost/', CreatePostView.as_view(), name='createpost'),
]