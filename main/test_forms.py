from django.test import TestCase
from .forms import CommentForm, PostForm
from django.contrib.auth.models import User
from .models import Post, Comment

class CommentFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.post = Post.objects.create(title='Test Post', content='Post content', user=self.user)

    def test_comment_form_valid_data(self):
        form_data = {'content': 'Test comment content'}
        form = CommentForm(data=form_data, instance=Comment(user=self.user, post=self.post))
        self.assertTrue(form.is_valid())

    def test_comment_form_save(self):
        form_data = {'content': 'Test comment content'}
        form = CommentForm(data=form_data, instance=Comment(user=self.user, post=self.post))
        if form.is_valid():
            comment = form.save()
            self.assertEqual(comment.content, 'Test comment content')
            self.assertEqual(comment.user, self.user)
            self.assertEqual(comment.post, self.post)

    def test_comment_form_empty_content(self):
        form_data = {'content': ''}
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

class PostFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')

    def test_post_form_valid_data(self):
        form_data = {
            'title': 'Test Title',
            'content': 'Test Content',
            'extra_info': 'Some extra info'
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_form_save(self):
        form_data = {
            'title': 'Test Title',
            'content': 'Test Content',
            'extra_info': 'Some extra info'
        }
        form = PostForm(data=form_data)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = self.user
            post.save()
            self.assertEqual(Post.objects.count(), 1)
            self.assertEqual(post.title, 'Test Title')
            self.assertEqual(post.content, 'Test Content')
            self.assertEqual(post.extra_info, 'Some extra info')

    def test_post_form_empty_fields(self):
        form_data = {
            'title': '',
            'content': '',
            'extra_info': ''
        }
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('content', form.errors)