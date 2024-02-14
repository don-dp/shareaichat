from django.test import TestCase
from django.contrib.auth.models import User
from .models import Post, PostVote, Comment, CommentVote, VoteTimestamp
from django.utils import timezone
from django.db import IntegrityError

class PostModelTestCase(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user(username='testuser', password='12345')
        self.test_post = Post.objects.create(
            title='Test Post Title',
            content='This is a test post content.',
            extra_info='Optional extra information',
            user=self.test_user,
            votes=10
        )

    def test_post_str_method(self):
        expected_object_name = self.test_post.title
        self.assertEqual(str(self.test_post), expected_object_name)

    def test_post_fields(self):
        self.assertEqual(self.test_post.title, 'Test Post Title')
        self.assertEqual(self.test_post.content, 'This is a test post content.')
        self.assertEqual(self.test_post.extra_info, 'Optional extra information')
        self.assertEqual(self.test_post.user.username, 'testuser')
        self.assertEqual(self.test_post.votes, 10)
        self.assertTrue(isinstance(self.test_post.created_at, timezone.datetime))
        self.assertTrue(isinstance(self.test_post.updated_at, timezone.datetime))

    def test_post_default_votes(self):
        new_user = User.objects.create_user(username='newuser', password='123456')
        new_post = Post.objects.create(
            title='Another Test Post',
            content='Content of the new test post.',
            user=new_user
        )
        self.assertEqual(new_post.votes, 1)

class PostVoteModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='test12345')
        self.user2 = User.objects.create_user(username='user2', password='test12345')

        self.post = Post.objects.create(
            title='Test Post',
            content='Just a test post.',
            user=self.user1
        )

    def test_post_vote_creation(self):
        vote = PostVote.objects.create(user=self.user1, post=self.post)
        self.assertTrue(isinstance(vote, PostVote))
        self.assertEqual(vote.__str__(), 'user1 upvoted Test Post')

    def test_unique_vote_per_user_post_combination(self):
        PostVote.objects.create(user=self.user1, post=self.post)
        
        with self.assertRaises(Exception):
            PostVote.objects.create(user=self.user1, post=self.post)

    def test_multiple_votes_different_users(self):
        vote1 = PostVote.objects.create(user=self.user1, post=self.post)
        vote2 = PostVote.objects.create(user=self.user2, post=self.post)

        self.assertNotEqual(vote1, vote2)
        self.assertEqual(PostVote.objects.count(), 2)

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test post content',
            user=self.user,
            votes=1
        )
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Test comment'
        )

    def test_is_root_comment(self):
        self.assertTrue(self.comment.is_root_comment())

    def test_comment_str(self):
        expected_str = f'{self.user.username} commented on {self.post.title}'
        self.assertEqual(str(self.comment), expected_str)

    def test_non_root_comment(self):
        child_comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            parent=self.comment,
            content='Child comment'
        )
        self.assertFalse(child_comment.is_root_comment())

class CommentVoteModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.other_user = User.objects.create_user(username='otheruser', password='54321')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test post content',
            user=self.user
        )
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Test comment'
        )

    def test_comment_vote_creation(self):
        comment_vote = CommentVote.objects.create(user=self.user, comment=self.comment)
        self.assertEqual(str(comment_vote), f'{self.user.username} upvoted a comment on {self.comment.post.title}')

    def test_unique_vote_per_user_comment_combination(self):
        CommentVote.objects.create(user=self.user, comment=self.comment)
        with self.assertRaises(IntegrityError):
            CommentVote.objects.create(user=self.user, comment=self.comment)

    def test_multiple_votes_different_users(self):
        first_vote = CommentVote.objects.create(user=self.user, comment=self.comment)
        second_vote = CommentVote.objects.create(user=self.other_user, comment=self.comment)
        self.assertNotEqual(first_vote, second_vote)
        self.assertEqual(CommentVote.objects.count(), 2)

class VoteTimestampModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_vote_timestamp_creation(self):
        vote_timestamp = VoteTimestamp.objects.create(user=self.user)
        self.assertTrue(isinstance(vote_timestamp, VoteTimestamp))

    def test_vote_timestamp_str(self):
        vote_timestamp = VoteTimestamp.objects.create(user=self.user)
        expected_str = f'{self.user.username} voted at {vote_timestamp.timestamp}'
        self.assertTrue(str(vote_timestamp).startswith(self.user.username))
