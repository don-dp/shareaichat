from django.contrib import admin
from .models import Post, PostVote, Comment, CommentVote, VoteTimestamp
from django import forms
from django.core.exceptions import ValidationError

class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)
    extra_info = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Post
        fields = '__all__'

class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'content',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Post, PostAdmin)

class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'votes', 'timestamp')
    search_fields = ('user__username', 'post__title')

    def votes(self, obj):
        return obj.post.votes
    votes.short_description = 'Votes'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('post')
        return queryset

admin.site.register(PostVote, PostVoteAdmin)

class CommentAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Comment
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        post = cleaned_data.get('post')

        if parent and parent.post != post:
            raise ValidationError("Parent comment's post and selected post must be the same.")

        return cleaned_data

class CommentAdmin(admin.ModelAdmin):
    form = CommentAdminForm
    list_display = ('user', 'post', 'parent', 'created_at', 'updated_at', 'votes')
    search_fields = ('user__username', 'post__title', 'content',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Comment, CommentAdmin)


class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'votes', 'timestamp')
    search_fields = ('user__username', 'comment__content')

    def votes(self, obj):
        return obj.comment.votes
    votes.short_description = 'Votes'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('comment')
        return queryset

admin.site.register(CommentVote, CommentVoteAdmin)

class VoteTimestampAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp')
    search_fields = ('user__username',)

admin.site.register(VoteTimestamp, VoteTimestampAdmin)