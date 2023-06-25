from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.core.paginator import Paginator
from .models import Post, PostVote, Comment, CommentVote, VoteTimestamp
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import defaultdict
from django.db.models import Count
from .forms import CommentForm, PostForm
from django.contrib import messages
from datetime import timedelta

class HomePage(View):
    def get(self, request):
        page_number = request.GET.get('page', 1)
        sort_by = request.GET.get('sort_by', 'trending')
        if sort_by not in ['new', 'trending']:
            sort_by = 'trending'
        time = request.GET.get('time', 'all_time')
        if time not in ['1_day', '7_days', '30_days', 'all_time']:
            time = 'all_time'

        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1
        
        page_size = 10

        if sort_by == 'new':
            posts = Post.objects.all().order_by('-created_at').annotate(comment_count=Count('comment'))
        else:
            if time == '1_day':
                date_limit = timezone.now() - timezone.timedelta(days=1)
            elif time == '7_days':
                date_limit = timezone.now() - timezone.timedelta(days=7)
            elif time == '30_days':
                date_limit = timezone.now() - timezone.timedelta(days=30)
            else:
                date_limit = None

            if date_limit:
                posts = Post.objects.filter(created_at__gte=date_limit).annotate(comment_count=Count('comment'))
            else:
                posts = Post.objects.all().annotate(comment_count=Count('comment'))

            posts = posts.order_by('-votes')

        paginator = Paginator(posts, page_size)
        posts = paginator.get_page(page_number)

        if request.user.is_authenticated:
            postvotes = PostVote.objects.filter(user=request.user, post__in=posts)
            upvoted_post_ids = postvotes.values_list('post', flat=True)
        else:
            upvoted_post_ids = []

        context = {'posts': posts, 'sort_by': sort_by, 'time' : time, 'upvoted_post_ids': upvoted_post_ids}
        return render(request, 'main/homepage.html', context)

class VotePostView(View):
    def post(self, request, post_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'You must be logged in to upvote.'}, status=401)
        
        # Check if the user has voted more than 10 times in the last 10 minutes
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        recent_votes = VoteTimestamp.objects.filter(user=request.user, timestamp__gte=ten_minutes_ago).count()
        old_votes = VoteTimestamp.objects.filter(timestamp__lt=ten_minutes_ago)
        old_votes.delete()

        if recent_votes > 10:
            return JsonResponse({'error': 'You have exceeded the vote limit.'}, status=429)

        try:
            post = Post.objects.get(pk=post_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid post id'}, status=400)

        user = request.user

        vote, created = PostVote.objects.get_or_create(user=user, post=post)

        VoteTimestamp.objects.create(user=request.user)

        if created:
            post.votes += 1
            post.save()
            return JsonResponse({'status': 'upvoted', 'post_id': post_id})

        else:
            vote.delete()
            post.votes -= 1
            post.save()
            return JsonResponse({'status': 'unvoted', 'post_id': post_id})

class PostDetailView(View):
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        comment_count = Comment.objects.filter(post=post).count()

        comments = Comment.objects.filter(post=post).order_by('-votes', 'created_at')

        root_comments = []
        child_comments = defaultdict(list)
        for comment in comments:
            if comment.is_root_comment():
                root_comments.append(comment)
            else:
                child_comments[comment.parent_id].append(comment)

        # Sort root comments by votes
        root_comments.sort(key=lambda x: x.votes, reverse=True)

        for comment in root_comments:
            comment.replies = sorted(child_comments[comment.id], key=lambda x: x.created_at)

        if request.user.is_authenticated:
            postvote = PostVote.objects.filter(user=request.user, post=post)
            is_upvoted = postvote.exists()

            commentvotes = CommentVote.objects.filter(user=request.user, comment__in=comments)
            upvoted_comment_ids = commentvotes.values_list('comment', flat=True)
        else:
            is_upvoted = False
            upvoted_comment_ids = []

        context = {
            'post': post,
            'is_upvoted': is_upvoted,
            'root_comments': root_comments,
            'upvoted_comment_ids' : upvoted_comment_ids,
            'comment_count' : comment_count,
            'form' : CommentForm(),
        }

        return render(request, 'main/post_detail.html', context)

class MyPostsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        my_posts_list = Post.objects.filter(user=request.user).annotate(comment_count=Count('comment')).order_by('-created_at')
        
        paginator = Paginator(my_posts_list, 10)
        my_posts = paginator.get_page(page_number)

        return render(request, 'main/myposts.html', {'my_posts': my_posts})

class MyCommentsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        my_comments_list = Comment.objects.filter(user=request.user).select_related('post').order_by('-created_at')


        paginator = Paginator(my_comments_list, 10)
        my_comments = paginator.get_page(page_number)

        return render(request, 'main/mycomments.html', {'my_comments': my_comments})

class VoteCommentView(View):
    def post(self, request, comment_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'You must be logged in to upvote.'}, status=401)

        # Check if the user has voted more than 10 times in the last 10 minutes
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        recent_votes = VoteTimestamp.objects.filter(user=request.user, timestamp__gte=ten_minutes_ago).count()
        old_votes = VoteTimestamp.objects.filter(timestamp__lt=ten_minutes_ago)
        old_votes.delete()

        if recent_votes > 10:
            return JsonResponse({'error': 'You have exceeded the vote limit.'}, status=429)

        try:
            comment = Comment.objects.get(pk=comment_id)
        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Invalid comment id'}, status=400)
        
        user = request.user

        vote, created = CommentVote.objects.get_or_create(user=user, comment=comment)

        VoteTimestamp.objects.create(user=request.user)

        if created:
            comment.votes += 1
            comment.save()
            return JsonResponse({'status': 'upvoted', 'comment_id': comment_id})

        else:
            vote.delete()
            comment.votes -= 1
            comment.save()
            return JsonResponse({'status': 'unvoted', 'comment_id': comment_id})

class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        form = CommentForm(request.POST)
        parent_id = request.GET.get('parent_id', None)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = get_object_or_404(Post, id=post_id)
            if parent_id is not None:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                if parent_comment.post.id != comment.post.id:
                    messages.error(request, "Parent comment does not belong to the current post.")
                    return redirect('post_detail', post_id=post_id)
                
                comment.parent = parent_comment
            comment.save()
            CommentVote.objects.create(user=request.user, comment=comment)
            messages.success(request, "Your comment has been added successfully.")
            return redirect('post_detail', post_id=post_id)
        
        messages.error(request, "There was an error adding your comment. Please try again.")
        return redirect('post_detail', post_id=post_id)

class ReplyCommentView(LoginRequiredMixin, View):
    def get(self, request, comment_id):
        initial_text = request.GET.get('initial_text', '')
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.is_root_comment():
            form = CommentForm(initial={'content': initial_text})
            return render(request, 'main/reply_comment.html', {'form': form, 'comment': comment})
        else:
            messages.error(request, 'You can only reply to root comments.')
            return redirect('post_detail', post_id=comment.post.id)

class EditCommentView(LoginRequiredMixin, View):
    def get(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user == request.user:
            form = CommentForm(instance=comment)
            return render(request, 'main/edit_comment.html', {'form': form, 'comment': comment})
        else:
            messages.error(request, 'You can only edit your own comments.')
            return redirect('post_detail', post_id=comment.post.id)

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user == request.user:
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
                messages.success(request, "Your comment has been updated successfully.")
                return redirect('post_detail', post_id=comment.post.id)
        else:
            messages.error(request, 'You can only edit your own comments.')
            return redirect('post_detail', post_id=comment.post.id)

class CreatePostView(LoginRequiredMixin, View):
    def get(self, request):
        form = PostForm()
        return render(request, 'main/create_post.html', {'form': form})

    def post(self, request):
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            PostVote.objects.create(user=request.user, post=post)
            messages.success(request, "Your post has been created successfully.")
            return redirect('post_detail', post_id=post.id)
        else:
            messages.error(request, 'There was an error creating your post.')
            return redirect('createpost')