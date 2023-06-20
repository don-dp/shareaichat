from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from .models import Post, PostVote
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

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
            posts = Post.objects.all().order_by('-created_at')
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
                posts = Post.objects.filter(created_at__gte=date_limit)
            else:
                posts = Post.objects.all()

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
            return JsonResponse({'error': 'You must be logged in to upvote.'})

        try:
            post = Post.objects.get(pk=post_id)
        except Exception as e:
            return JsonResponse({'error': 'Invalid post id'}, status=400)

        user = request.user

        vote, created = PostVote.objects.get_or_create(user=user, post=post)

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
        
        if request.user.is_authenticated:
            postvotes = PostVote.objects.filter(user=request.user, post=post)
            is_upvoted = postvotes.exists()
        else:
            is_upvoted = False
        
        context = {
            'post': post,
            'is_upvoted': is_upvoted,
        }

        return render(request, 'main/post_detail.html', context)

class MyPostsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1

        my_posts_list = Post.objects.filter(user=request.user).order_by('-created_at')
        
        paginator = Paginator(my_posts_list, 10)
        my_posts = paginator.get_page(page_number)

        return render(request, 'main/myposts.html', {'my_posts': my_posts})