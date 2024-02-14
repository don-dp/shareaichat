from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, PostVote, VoteTimestamp, Comment, CommentVote
from django.utils import timezone
from datetime import timedelta
from .forms import CommentForm
from django.contrib.messages import get_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count

class HomePageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.url = reverse('homepage')

    def test_home_page_without_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/homepage.html')
        self.assertIn('posts', response.context)

    def test_home_page_sort_by_new(self):
        Post.objects.create(title='Post 1', content='Content 1', user=self.user, votes=10)
        Post.objects.create(title='Post 2', content='Content 2', user=self.user, votes=5)
        response = self.client.get(self.url, {'sort_by': 'new'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 2)
        self.assertEqual(response.context['posts'].number, 1)  # Page number
        self.assertEqual(response.context['sort_by'], 'new')

    def test_home_page_sort_by_trending_with_time_filter(self):
        post1 = Post.objects.create(
            title='Post 1',
            content='Content 1',
            user=self.user,
            votes=10,
            created_at=timezone.now() - timedelta(days=2)
        )
        post2 = Post.objects.create(
            title='Post 2',
            content='Content 2',
            user=self.user,
            votes=5,
            created_at=timezone.now() - timedelta(days=9)
        )

        # Adjust created_at after initial creation
        post1.created_at = timezone.now() - timedelta(days=2)
        post1.save(update_fields=['created_at'])
        post2.created_at = timezone.now() - timedelta(days=9)
        post2.save(update_fields=['created_at'])

        response = self.client.get(self.url, {'sort_by': 'trending', 'time': '7_days'})

        self.assertEqual(response.status_code, 200)
        self.assertIn(post1, response.context['posts'])
        self.assertNotIn(post2, response.context['posts'])

    def test_home_page_pagination(self):
        for i in range(15):
            Post.objects.create(title=f'Post {i}', content=f'Content {i}', user=self.user, votes=i)
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 5)

class VotePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user, votes=0)
        self.url = reverse('vote_post', args=[self.post.pk])

    def test_vote_without_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_exceed_vote_limit(self):
        self.client.force_login(self.user)
        for _ in range(11):
            VoteTimestamp.objects.create(user=self.user, timestamp=timezone.now())
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 429)

    def test_invalid_post_id(self):
        self.client.force_login(self.user)
        invalid_url = reverse('vote_post', args=[99999])  # Assuming 99999 is an invalid post ID
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 400)

    def test_successful_upvote(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.post.refresh_from_db()  # Refresh to get updated votes count
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.votes, 1)

    def test_toggle_vote(self):
        self.client.force_login(self.user)
        # First vote
        self.client.post(self.url)
        # Toggle vote
        response = self.client.post(self.url)
        self.post.refresh_from_db()  # Refresh to get updated votes count
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.votes, 0)

class PostDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user)
        self.url = reverse('post_detail', args=[self.post.id])

    def test_post_detail_view_with_invalid_post_id(self):
        invalid_url = reverse('post_detail', args=[99999])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_post_detail_view_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_upvoted' in response.context)
        self.assertTrue('can_delete' in response.context)
        self.assertTrue('root_comments' in response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertFalse(response.context['is_upvoted'])  # Assuming user hasn't voted yet

    def test_post_detail_view_for_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_upvoted', response.context)
        self.assertFalse(response.context['is_upvoted'])


    def test_comment_and_vote_display_for_authenticated_user(self):
        # Create comments and votes to test the display logic
        comment = Comment.objects.create(user=self.user, post=self.post, content='A comment')
        CommentVote.objects.create(user=self.user, comment=comment)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertIn(comment.id, response.context['upvoted_comment_ids'])
        self.assertIn(comment, response.context['root_comments'])

    def test_post_deletion_permission_within_one_hour(self):
        # Assume post was created less than an hour ago
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.context['can_delete'])

class MyPostsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass2')
        self.url = reverse('myposts')

        for i in range(15):
            Post.objects.create(title=f'Post {i}', content='Test Content', user=self.user)

    def test_access_by_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('my_posts' in response.context)
        self.assertTrue(all(post.user == self.user for post in response.context['my_posts']))

    def test_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['my_posts']), 5)

    def test_access_by_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(response.status_code, 302)
        self.assertTrue('/login' in response.url)

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, Comment

class MyCommentsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user2 = User.objects.create_user(username='otheruser', password='otherpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user2)
        self.url = reverse('mycomments')

        for i in range(15):
            Comment.objects.create(user=self.user, post=self.post, content=f'Comment {i}')

    def test_access_by_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('my_comments' in response.context)
        self.assertTrue(all(comment.user == self.user for comment in response.context['my_comments']))

    def test_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['my_comments']), 5)

    def test_access_by_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.url)

class VoteCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user)
        self.comment = Comment.objects.create(user=self.other_user, post=self.post, content='A comment')
        self.url = reverse('vote_comment', args=[self.comment.pk])

    def test_vote_without_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_exceed_vote_limit(self):
        self.client.force_login(self.user)
        for _ in range(11):
            VoteTimestamp.objects.create(user=self.user, timestamp=timezone.now())
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 429)

    def test_invalid_comment_id(self):
        self.client.force_login(self.user)
        invalid_url = reverse('vote_comment', args=[99999])  # Assuming 99999 is an invalid comment ID
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 400)

    def test_successful_upvote(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.comment.refresh_from_db()  # Refresh to get updated votes count
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.comment.votes, 2)

    def test_toggle_vote(self):
        self.client.force_login(self.user)
        # First vote
        self.client.post(self.url)
        # Toggle vote
        response = self.client.post(self.url)
        self.comment.refresh_from_db()  # Refresh to get updated votes count
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.comment.votes, 1)

class AddCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user)
        self.comment = Comment.objects.create(user=self.user, post=self.post, content='Parent comment')
        self.url = reverse('add_comment', args=[self.post.id])

    def test_comment_creation_by_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'content': 'A new comment'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 2)

    def test_comment_creation_by_unauthenticated_user(self):
        response = self.client.post(self.url, {'content': 'A new comment'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response['Location'])

    def test_invalid_comment_data(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'content': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)

    def test_nested_comment_creation(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url + f'?parent_id={self.comment.id}', {'content': 'A reply comment'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.filter(parent=self.comment).count(), 1)

    def test_nested_comment_wrong_parent(self):
        other_post = Post.objects.create(title='Other Post', content='Other Content', user=self.user)
        self.client.force_login(self.user)
        response = self.client.post(reverse('add_comment', args=[other_post.id]) + f'?parent_id={self.comment.id}', {'content': 'A reply comment'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.filter(parent=self.comment).count(), 0)

class ReplyCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user)
        self.root_comment = Comment.objects.create(user=self.user, post=self.post, content='Root comment')
        self.child_comment = Comment.objects.create(user=self.user, post=self.post, content='Child comment', parent=self.root_comment)
        self.root_comment_url = reverse('reply_comment', args=[self.root_comment.pk])
        self.child_comment_url = reverse('reply_comment', args=[self.child_comment.pk])

    def test_reply_to_root_comment_by_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.root_comment_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertEqual(response.context['comment'], self.root_comment)

    def test_attempt_reply_to_child_comment(self):
        self.client.force_login(self.user)
        response = self.client.get(self.child_comment_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('post_detail', args=[self.post.id]))

    def test_reply_with_invalid_comment_id(self):
        self.client.force_login(self.user)
        invalid_comment_url = reverse('reply_comment', args=[99999])
        response = self.client.get(invalid_comment_url)
        self.assertEqual(response.status_code, 404)

    def test_access_by_unauthenticated_user(self):
        response = self.client.get(self.root_comment_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.url)

class EditCommentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user)
        self.comment = Comment.objects.create(user=self.user, post=self.post, content='Original comment')
        self.url = reverse('edit_comment', args=[self.comment.pk])

    def test_edit_own_comment_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/edit_comment.html')
        self.assertEqual(response.context['comment'], self.comment)

    def test_attempt_edit_another_users_comment(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('post_detail', args=[self.post.id]))

    def test_edit_own_comment_post_valid(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'content': 'Updated comment'})
        self.comment.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.comment.content, 'Updated comment')
        
    def test_edit_comment_invalid_comment_id(self):
        self.client.force_login(self.user)
        invalid_comment_url = reverse('edit_comment', args=[99999])
        response = self.client.get(invalid_comment_url)
        self.assertEqual(response.status_code, 404)

    def test_access_by_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login' in response.url)

class CreatePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('createpost')

    def test_get_form_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/create_post.html')
        self.assertIsNotNone(response.context['form'])

    def test_access_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(response.status_code, 302)

    def test_post_valid_data(self):
        self.client.force_login(self.user)
        post_count_before = Post.objects.count()
        response = self.client.post(self.url, {'title': 'New Post Title', 'content': 'New post content'})
        post_count_after = Post.objects.count()

        self.assertEqual(post_count_after, post_count_before + 1)
        self.assertEqual(response.status_code, 302)
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.title, 'New Post Title')
        self.assertTrue(PostVote.objects.filter(user=self.user, post=new_post).exists())

    def test_post_invalid_data(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'title': '', 'content': ''})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(["error" in str(message) for message in messages]))
        self.assertEqual(response.status_code, 302)

class PostDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')
        self.post = Post.objects.create(title='Test Post', content='Test Content', user=self.user, created_at=timezone.now() - timedelta(minutes=30))
        self.url = reverse('post_delete', args=[self.post.id])

    def test_delete_unauthenticated_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_delete_other_users_post(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_after_one_hour(self):
        # Adjust the post's created_at to simulate it being older than 1 hour
        self.post.created_at -= timedelta(hours=1, minutes=1)
        self.post.save()
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_successful_post_deletion(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_delete_nonexistent_post(self):
        self.client.force_login(self.user)
        nonexistent_url = reverse('post_delete', args=[99999])
        response = self.client.post(nonexistent_url)
        self.assertEqual(response.status_code, 404)
